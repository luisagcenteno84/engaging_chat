# EngagingChat

A curiosity-first, fact-based learning chatbot with streaks, points, memory, and topic bubbles.

## Structure
- `C:\git\engaging_chat\frontend_streamlit` Streamlit UI
- `C:\git\engaging_chat\backend` FastAPI API with Firestore + OpenAI
- `C:\git\engaging_chat\deploy` GCP deployment helpers

## Backend

### Setup
1. Copy `C:\git\engaging_chat\backend\.env.example` to `.env` and fill values.
2. Install deps:

```bash
pip install -r C:\git\engaging_chat\backend\requirements.txt
```

### Run locally

```bash
uvicorn app.main:app --reload --port 8080 --app-dir C:\git\engaging_chat\backend
```

## Frontend (Streamlit)

### Setup
1. Copy `C:\git\engaging_chat\frontend_streamlit\.env.example` to `.env` and point to the API.
2. Install deps:

```bash
pip install -r C:\git\engaging_chat\frontend_streamlit\requirements.txt
```

### Run locally

```bash
streamlit run C:\git\engaging_chat\frontend_streamlit\app.py
```

## Firestore Collections
- `users`
- `conversations` (with `turns` subcollection)
- `daily_usage`
- `topics` (reserved for future)

## Deployment (GCP Free Tier)
See `C:\git\engaging_chat\deploy\gcp.md` for Cloud Run + Firebase Hosting steps.
