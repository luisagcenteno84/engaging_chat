from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    user_id: str
    created_at: datetime
    points: int = 0
    current_streak: int = 0
    last_active_date: str | None = None
    topics_of_interest: List[str] = Field(default_factory=list)


class ConversationTurn(BaseModel):
    conversation_id: str
    timestamp: datetime
    topic: str
    question: str
    user_answer: str
    correct_answer: str | None = None
    was_correct: bool | None = None


class DailyUsage(BaseModel):
    date: str
    user_id: str
    messages_sent: int = 0
    points_earned: int = 0


class ChatRequest(BaseModel):
    user_id: str | None = None
    topic: str | None = None
    user_message: str | None = None
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    user_id: str
    bot_message: str
    response_bubbles: List[str]
    points_awarded: int = 0
    total_points: int = 0
    current_streak: int = 0
    topics_of_interest: List[str] = Field(default_factory=list)


class ProfileResponse(BaseModel):
    user: UserProfile

class BlogDraftRequest(BaseModel):
    user_id: str | None = None
    conversation_id: str | None = None
    help_level: str = 'medium'
    seed_idea: str | None = None


class BlogPublishRequest(BaseModel):
    blog_id: str


class BlogPostSummary(BaseModel):
    blog_id: str
    title: str
    status: str
    created_at: datetime
    published_at: datetime | None = None


class BlogPostResponse(BaseModel):
    blog_id: str
    user_id: str
    title: str
    content: str
    status: str
    help_level: str
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    source_conversation_id: str | None = None
    source_turn_id: str | None = None

