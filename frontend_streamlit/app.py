import os
import uuid
import requests
import streamlit as st
import streamlit.components.v1 as components


API_URL = os.getenv('API_URL', 'http://localhost:8080')

TOPICS = [
    'Philosophy',
    'History',
    'Mathematics',
    'Science',
    'Surprise me'
]

EXTRA_TOPICS = [
    'Literature',
    'Psychology',
    'Economics',
    'Political Science',
    'Anthropology',
    'Physics',
    'Astronomy',
    'Biology',
    'Computer Science',
    'AI',
    'Logic Puzzles',
    'Trivia',
    'Ethical Dilemmas',
    'Stoicism',
    'Game Theory'
]


def init_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                'id': 'intro',
                'role': 'assistant',
                'text': 'What do you want to chat about today?',
                'bubbles': TOPICS
            }
        ]
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
    if 'points' not in st.session_state:
        st.session_state.points = 0
    if 'streak' not in st.session_state:
        st.session_state.streak = 0
    if 'topics' not in st.session_state:
        st.session_state.topics = []
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None
    if 'blog_draft_id' not in st.session_state:
        st.session_state.blog_draft_id = None
    if 'blog_draft_title' not in st.session_state:
        st.session_state.blog_draft_title = None
    if 'blog_draft_content' not in st.session_state:
        st.session_state.blog_draft_content = None
    if 'selected_blog_id' not in st.session_state:
        st.session_state.selected_blog_id = None


def send_message(text, topic=None):
    payload = {
        'user_id': st.session_state.user_id,
        'topic': topic,
        'user_message': text,
        'conversation_id': st.session_state.conversation_id
    }

    st.session_state.loading = True
    st.session_state.last_error = None
    try:
        response = requests.post(f"{API_URL}/chat", json=payload, timeout=30)
        if not response.ok:
            st.session_state.last_error = f"API error {response.status_code}: {response.text[:200]}"
            response.raise_for_status()
        data = response.json()

        if not st.session_state.user_id:
            st.session_state.user_id = data.get('user_id')

        st.session_state.conversation_id = data.get('conversation_id')
        st.session_state.points = data.get('total_points', 0)
        st.session_state.streak = data.get('current_streak', 0)
        st.session_state.topics = data.get('topics_of_interest', [])

        if text:
            st.session_state.messages.append({
                'id': str(uuid.uuid4()),
                'role': 'user',
                'text': text
            })

        st.session_state.messages.append({
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'text': data.get('bot_message', ''),
            'bubbles': data.get('response_bubbles', [])
        })
    except Exception as exc:
        if not st.session_state.last_error:
            st.session_state.last_error = str(exc)
        st.session_state.messages.append({
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'text': 'Something went wrong. Try again?'
        })
    finally:
        st.session_state.loading = False


def create_blog_draft(help_level: str, seed_idea: str | None = None):
    payload = {
        'user_id': st.session_state.user_id,
        'conversation_id': st.session_state.conversation_id,
        'help_level': help_level,
        'seed_idea': seed_idea,
    }
    try:
        response = requests.post(f"{API_URL}/blog/draft", json=payload, timeout=60)
        if not response.ok:
            st.session_state.last_error = f"Blog draft failed: {response.status_code} {response.text[:200]}"
            response.raise_for_status()
        data = response.json()
        st.session_state.blog_draft_id = data.get('blog_id')
        st.session_state.blog_draft_title = data.get('title')
        st.session_state.blog_draft_content = data.get('content')
        st.session_state.page = 'Blog'
    except Exception as exc:
        if not st.session_state.last_error:
            st.session_state.last_error = f"Blog draft failed: {exc}"


def publish_blog():
    if not st.session_state.blog_draft_id:
        st.session_state.last_error = "No draft available to publish."
        return
    payload = {'blog_id': st.session_state.blog_draft_id}
    try:
        response = requests.post(f"{API_URL}/blog/publish", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        st.session_state.blog_draft_title = data.get('title')
        st.session_state.blog_draft_content = data.get('content')
        st.session_state.page = 'Blog'
    except Exception as exc:
        st.session_state.last_error = f"Blog publish failed: {exc}"


init_state()

st.set_page_config(page_title='EngagingChat', page_icon='?', layout='wide')

st.markdown(
    """
    <style>
    :root {
      color-scheme: light;
    }
    .stApp {
      background:
        radial-gradient(circle at 12% 10%, rgba(186, 230, 253, 0.75), transparent 45%),
        radial-gradient(circle at 85% 15%, rgba(167, 243, 208, 0.7), transparent 50%),
        linear-gradient(180deg, #f0f9ff 0%, #ecfeff 45%, #f0fdf4 100%);
      color: #0f172a;
    }
    .block-container {
      padding-top: 1.5rem;
      padding-bottom: 2.5rem;
    }
    .stSidebar > div:first-child {
      background: rgba(240, 249, 255, 0.95);
      border-right: 1px solid rgba(14, 116, 144, 0.15);
    }
    .chat-area {
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid rgba(14, 116, 144, 0.15);
      border-radius: 18px;
      padding: 1rem;
      box-shadow: 0 18px 36px rgba(14, 116, 144, 0.12);
    }
    .topic-chip button {
      border-radius: 999px !important;
      border: 1px solid rgba(14, 116, 144, 0.2) !important;
      background: rgba(255, 255, 255, 0.9) !important;
      color: #0f172a !important;
    }
    .topic-chip button:hover {
      background: rgba(224, 242, 254, 0.9) !important;
      border-color: rgba(14, 116, 144, 0.35) !important;
    }
    .stButton > button {
      color: #0f172a;
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid rgba(14, 116, 144, 0.2);
    }
    .stButton > button:hover {
      background: rgba(224, 242, 254, 0.9);
      border-color: rgba(14, 116, 144, 0.35);
    }
    .stMetric {
      background: rgba(255, 255, 255, 0.8);
      border: 1px solid rgba(14, 116, 144, 0.15);
      border-radius: 16px;
      padding: 0.4rem 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('Curiosity Chat')
st.caption('Socratic, fact-based learning with streaks and points.')

with st.sidebar:
    st.header('Your Progress')
    page = st.radio('View', ['Chat', 'Blog'], index=0, key='page')
    st.metric('Streak (days)', st.session_state.streak)
    st.metric('Points', st.session_state.points)
    st.divider()
    st.subheader('Blog tools')
    st.caption('Draft and publish a blog post from this conversation.')
    help_level = st.selectbox('Draft help level', ['minimal', 'medium', 'a lot'], index=1, key='blog_help_level')
    seed_idea = st.text_input('Seed idea (optional)', key='blog_seed_idea')
    if st.button('Draft blog post'):
        create_blog_draft(help_level, seed_idea or None)
        st.experimental_rerun()
    publish_disabled = st.session_state.blog_draft_id is None
    if st.button('Publish blog post', disabled=publish_disabled):
        publish_blog()
        st.experimental_rerun()
    st.divider()
    st.subheader('Topics explored')
    if st.session_state.topics:
        for topic in st.session_state.topics:
            st.write(f"? {topic}")
    else:
        st.caption('None yet')
    st.divider()
    st.subheader('Try a new lane')
    for idx, topic in enumerate(EXTRA_TOPICS):
        st.button(topic, key=f"side-topic-{idx}", on_click=send_message, args=(topic, topic))
    
if page == 'Chat':
        st.markdown('<div class="chat-area">', unsafe_allow_html=True)

        for message in st.session_state.messages:
            with st.chat_message(message['role']):
                st.write(message['text'])

        if st.session_state.loading:
            st.info('Thinking...')

        last_bubbles = st.session_state.messages[-1].get('bubbles', [])
        if last_bubbles:
            st.markdown('**Suggested replies**')
            bubble_cols = st.columns(4)
            for idx, bubble in enumerate(last_bubbles):
                col = bubble_cols[idx % 4]
                with col:
                    st.markdown('<div class="topic-chip">', unsafe_allow_html=True)
                    if st.button(bubble, key=f"bubble-{bubble}-{idx}"):
                        if bubble == 'Draft blog post':
                            create_blog_draft(st.session_state.get('blog_help_level', 'medium'))
                        elif bubble == 'Publish blog post':
                            publish_blog()
                        else:
                            is_topic = bubble in TOPICS or bubble in EXTRA_TOPICS
                            send_message(bubble, bubble if is_topic else None)
                        st.experimental_rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        user_input = st.chat_input('Ask a question or pick a topic above')
        if user_input:
            send_message(user_input)
            st.experimental_rerun()




if page == 'Blog':
        st.title('Blog Posts')
        st.caption('Published posts are listed newest first.')
        try:
            resp = requests.get(f"{API_URL}/blog", params={'status': 'published', 'limit': 50}, timeout=15)
            resp.raise_for_status()
            posts = resp.json()
        except Exception:
            posts = []

        if posts:
            posts = sorted(posts, key=lambda p: p.get('created_at') or '', reverse=True)
            options = {f"{p['title']} ? {str(p.get('created_at', ''))[:10]}": p['blog_id'] for p in posts}
            selected = st.selectbox('Select a post', list(options.keys()))
            blog_id = options.get(selected)
            if blog_id:
                try:
                    detail = requests.get(f"{API_URL}/blog/{blog_id}", timeout=15).json()
                    st.markdown(f"## {detail.get('title', 'Untitled')}")
                    created_at = str(detail.get('created_at', ''))
                    if created_at:
                        st.caption(f"Created: {created_at}")
                    st.write(detail.get('content', ''))
                except Exception:
                    st.caption('Unable to load blog post.')
        else:
            st.caption('No published posts yet.')
# Keep focus on the input for quick follow-ups.
components.html(
    """
    <script>
      const focusInput = () => {
        const el = window.parent.document.querySelector('textarea');
        if (el) { el.focus(); }
      };
      setTimeout(focusInput, 50);
    </script>
    """,
    height=0,
)
if st.session_state.last_error:
    st.error(f"Request failed: {st.session_state.last_error}")

