from __future__ import annotations

import re
import uuid
import time
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from google.api_core.exceptions import GoogleAPIError, PermissionDenied, FailedPrecondition
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import get_client, now_utc, iso_date
from .models import (
    ChatRequest,
    ChatResponse,
    ProfileResponse,
    UserProfile,
    BlogDraftRequest,
    BlogPublishRequest,
    BlogPostSummary,
    BlogPostResponse,
)
from .llm_client import chat_completion, health_check
from .points import (
    calculate_streak,
    normalize_topic,
    points_for_correct,
    points_for_daily_login,
    today_iso,
)
from .prompts import build_messages

app = FastAPI(title='EngagingChat API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)



@app.on_event('startup')
def verify_firestore_ready():
    # Fail fast if Firestore is disabled or credentials are missing.
    try:
        db = get_client()
        # Force a lightweight call to verify permissions.
        _ = list(db.collection('users').limit(1).stream())
    except PermissionDenied as exc:
        raise RuntimeError(
            "Firestore API is disabled or access is denied for the configured project. "
            "Enable Cloud Firestore API in the Google Cloud Console and ensure "
            "Application Default Credentials are set."
        ) from exc
    except GoogleAPIError as exc:
        raise RuntimeError(
            "Failed to initialize Firestore. Check credentials, project ID, and network access."
        ) from exc

OPTION_PREFIX = re.compile(r'^(?:[-*]|\d+\.)\s*(.+)$')
CORRECT_TAG = re.compile(r'^\s*Correct answer\s*:\s*(.+)$', re.IGNORECASE)


@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/health/llm')
def health_llm():
    try:
        return health_check()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM health check failed: {exc}")

@app.get('/health/openai')
def health_openai():
    if settings.llm_provider.strip().lower() not in {'openai', 'openai_compatible'}:
        raise HTTPException(status_code=400, detail='OpenAI health endpoint is disabled when LLM_PROVIDER is not openai.')
    try:
        return health_check()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI health check failed: {exc}")




@app.get('/profile/{user_id}', response_model=ProfileResponse)
def get_profile(user_id: str):
    db = get_client()
    doc = db.collection('users').document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail='User not found')
    return ProfileResponse(user=UserProfile(**doc.to_dict()))


def ensure_user(user_id: str | None) -> UserProfile:
    db = get_client()
    if not user_id:
        if not settings.allow_guest:
            raise HTTPException(status_code=400, detail='user_id required')
        user_id = str(uuid.uuid4())

    user_ref = db.collection('users').document(user_id)
    snapshot = user_ref.get()
    if snapshot.exists:
        return UserProfile(**snapshot.to_dict())

    created = UserProfile(
        user_id=user_id,
        created_at=now_utc(),
        points=0,
        current_streak=0,
        last_active_date=None,
        topics_of_interest=[],
    )
    user_ref.set(created.model_dump())
    return created


def load_recent_history(conversation_id: str, limit: int = 6) -> List[dict]:
    db = get_client()
    turns_ref = (
        db.collection('conversations')
        .document(conversation_id)
        .collection('turns')
        .order_by('timestamp', direction='DESCENDING')
        .limit(limit)
    )
    docs = list(turns_ref.stream())
    history: List[dict] = []
    for doc in reversed(docs):
        data = doc.to_dict()
        history.append({"role": "assistant", "content": data.get('question', '')})
        if data.get('user_answer'):
            history.append({"role": "user", "content": data.get('user_answer', '')})
    return history


def parse_response_bubbles(text: str) -> List[str]:
    options: List[str] = []
    for line in text.splitlines():
        match = OPTION_PREFIX.match(line.strip())
        if match:
            opt = match.group(1).strip()
            if opt:
                options.append(opt)
    # Ensure required bubbles
    required = ["I don't know", "Different subject"]
    for req in required:
        if req not in options:
            options.append(req)
    # Keep options short and focused
    cleaned: List[str] = []
    for opt in options:
        trimmed = opt.strip()
        if len(trimmed) > 48:
            continue
        cleaned.append(trimmed)
    # De-duplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for opt in cleaned:
        if opt.lower() in seen:
            continue
        seen.add(opt.lower())
        deduped.append(opt)
    return deduped[:6]



def strip_correct_answer(text: str) -> tuple[str, str | None]:
    correct = None
    cleaned_lines: List[str] = []
    for line in text.splitlines():
        tag = CORRECT_TAG.match(line)
        if tag:
            correct = tag.group(1).strip()
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines).strip()
    return cleaned, correct


def is_correct(user_message: str | None, correct_answer: str | None) -> bool | None:
    if not user_message or not correct_answer:
        return None
    return user_message.strip().lower() == correct_answer.strip().lower()


def update_daily_usage(user: UserProfile, points_earned: int) -> int:
    db = get_client()
    today = today_iso()
    doc_id = f"{user.user_id}_{today}"
    usage_ref = db.collection('daily_usage').document(doc_id)
    snapshot = usage_ref.get()

    if snapshot.exists:
        usage = snapshot.to_dict()
        usage['messages_sent'] = usage.get('messages_sent', 0) + 1
        usage['points_earned'] = usage.get('points_earned', 0) + points_earned
        usage_ref.set(usage)
        return 0

    usage_ref.set({
        'date': today,
        'user_id': user.user_id,
        'messages_sent': 1,
        'points_earned': points_earned,
    })
    return points_for_daily_login()


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest):
    user = ensure_user(payload.user_id)
    request_id = str(uuid.uuid4())
    topic = normalize_topic(payload.topic)
    conversation_id = payload.conversation_id or str(uuid.uuid4())

    history = load_recent_history(conversation_id)
    messages = build_messages(topic, history, user.model_dump(), payload.user_message)

    start_time = time.perf_counter()
    try:
        ai_text = chat_completion(messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}")
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    ai_text, correct_answer = strip_correct_answer(ai_text)

    bubbles = parse_response_bubbles(ai_text)
    for special in ['Draft blog post', 'Publish blog post']:
        if special not in bubbles:
            bubbles.append(special)

    was_correct = is_correct(payload.user_message, correct_answer)
    points_awarded = 0
    if was_correct is True:
        points_awarded += points_for_correct()

    daily_bonus = update_daily_usage(user, points_awarded)
    points_awarded += daily_bonus

    today = iso_date()
    streak_delta = calculate_streak(user.last_active_date, today)
    if streak_delta == 1:
        user.current_streak += 1
    elif streak_delta == -1:
        user.current_streak = 1

    if streak_delta != 0:
        user.last_active_date = today

    user.points += points_awarded

    if topic not in user.topics_of_interest:
        user.topics_of_interest.append(topic)

    llm_provider = settings.llm_provider.strip().lower() if settings.llm_provider else 'gemini'
    llm_model = settings.gemini_model if llm_provider == 'gemini' else settings.openai_model

    db = get_client()
    db.collection('users').document(user.user_id).set(user.model_dump())

    turn = {
        'request_id': request_id,
        'conversation_id': conversation_id,
        'user_id': user.user_id,
        'timestamp': now_utc(),
        'topic': topic,
        'question': ai_text,
        'user_answer': payload.user_message or '',
        'bot_message': ai_text,
        'response_bubbles': bubbles,
        'correct_answer': correct_answer,
        'was_correct': was_correct,
        'llm_provider': llm_provider,
        'llm_model': llm_model,
        'llm_latency_ms': latency_ms,
    }

    db.collection('conversations').document(conversation_id).set({
        'conversation_id': conversation_id,
        'user_id': user.user_id,
        'topic': topic,
        'updated_at': now_utc(),
        'last_user_message': payload.user_message or '',
        'last_bot_message': ai_text,
        'last_turn_at': now_utc(),
        'llm_provider': llm_provider,
        'llm_model': llm_model,
    }, merge=True)

    db.collection('conversations').document(conversation_id).collection('turns').add(turn)
    db.collection('turns').document(request_id).set(turn)

    return ChatResponse(
        conversation_id=conversation_id,
        user_id=user.user_id,
        bot_message=ai_text,
        response_bubbles=bubbles,
        points_awarded=points_awarded,
        total_points=user.points,
        current_streak=user.current_streak,
        topics_of_interest=user.topics_of_interest,
    )




def build_blog_prompt(help_level: str, seed_idea: str | None, history: List[dict]) -> list[dict]:
    level = (help_level or 'medium').strip().lower()
    help_map = {
        'minimal': "Light guidance only. Provide a short outline and a concise draft.",
        'medium': "Balanced guidance. Provide a clear outline and a solid draft.",
        'lot': "Heavy guidance. Provide a detailed outline, suggested headings, and a thorough draft.",
        'a lot': "Heavy guidance. Provide a detailed outline, suggested headings, and a thorough draft.",
    }
    guidance = help_map.get(level, help_map['medium'])

    system = (
        "You are a writing assistant drafting a blog post in a casual, mid-40s executive tone. "
        "Keep it concise and practical. Provide a clear title and draft content. "
        "Do not fabricate sources or quotes."
    )

    seed_line = f"Seed idea: {seed_idea}." if seed_idea else "Seed idea: Use the most recent conversation context."
    prompt = (
        f"Create a blog post draft. {seed_line} "
        f"Guidance level: {guidance} "
        "Return in the format:\n"
        "Title: <title>\n\n"
        "Draft:\n<content>"
    )

    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": prompt})
    return messages


@app.post('/blog/draft', response_model=BlogPostResponse)
def create_blog_draft(payload: BlogDraftRequest):
    db = get_client()
    blog_id = str(uuid.uuid4())
    history = []
    if payload.conversation_id:
        history = load_recent_history(payload.conversation_id, limit=6)

    messages = build_blog_prompt(payload.help_level, payload.seed_idea, history)
    try:
        draft_text = chat_completion(messages)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}")

    title = "Untitled"
    content = draft_text
    if "Title:" in draft_text:
        parts = draft_text.split("Title:", 1)[1].strip().split("Draft:", 1)
        if parts:
            title = parts[0].strip() or title
        if len(parts) > 1:
            content = parts[1].strip() or content

    now = now_utc()
    doc = {
        'blog_id': blog_id,
        'user_id': payload.user_id,
        'title': title,
        'content': content,
        'status': 'draft',
        'help_level': payload.help_level or 'medium',
        'created_at': now,
        'updated_at': now,
        'published_at': None,
        'source_conversation_id': payload.conversation_id,
        'source_turn_id': None,
    }
    db.collection('blog_posts').document(blog_id).set(doc)
    return BlogPostResponse(**doc)


@app.post('/blog/publish', response_model=BlogPostResponse)
def publish_blog(payload: BlogPublishRequest):
    db = get_client()
    ref = db.collection('blog_posts').document(payload.blog_id)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail='Blog post not found')

    now = now_utc()
    updates = {
        'status': 'published',
        'published_at': now,
        'updated_at': now,
    }
    ref.set(updates, merge=True)
    data = ref.get().to_dict()
    return BlogPostResponse(**data)


@app.get('/blog', response_model=List[BlogPostSummary])
def list_blogs(status: str = 'published', limit: int = 20):
    db = get_client()
    posts = []
    try:
        query = (
            db.collection('blog_posts')
            .where('status', '==', status)
            .order_by('created_at', direction='DESCENDING')
            .limit(limit)
        )
        docs = query.stream()
    except FailedPrecondition:
        docs = db.collection('blog_posts').where('status', '==', status).stream()

    for doc in docs:
        data = doc.to_dict()
        posts.append(BlogPostSummary(
            blog_id=data.get('blog_id', doc.id),
            title=data.get('title', 'Untitled'),
            status=data.get('status', 'draft'),
            created_at=data.get('created_at'),
            published_at=data.get('published_at'),
        ))

    posts.sort(key=lambda p: p.created_at or now_utc(), reverse=True)
    return posts[:limit]


@app.get('/blog/{blog_id}', response_model=BlogPostResponse)
def get_blog(blog_id: str):
    db = get_client()
    snap = db.collection('blog_posts').document(blog_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail='Blog post not found')
    return BlogPostResponse(**snap.to_dict())


