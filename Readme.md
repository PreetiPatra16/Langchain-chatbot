# AI Chatbot

A conversational AI chatbot built with **Streamlit**, **FastAPI**, and **Google Gemini**, with full conversation persistence via **Supabase**.

## Features

- **Multi-model support** — switch between Gemini models from the sidebar dropdown
- **Persistent conversations** — all sessions and messages stored in Supabase (PostgreSQL)
- **Session history** — resume any past conversation from the sidebar
- **Telemetry** — each response shows model used, token counts (in/out), and latency
- **Anonymous sessions** — no login required; sessions identified by UUID

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend API | FastAPI + Uvicorn |
| LLM | Google Gemini (`google-genai`) |
| Database | Supabase (PostgreSQL) |

## Supported Models

- `gemini-2.5-flash` (default)
- `gemini-2.5-pro`
- `gemini-2.0-flash`
- `gemini-2.0-flash-lite`
- `gemini-1.5-pro`
- `gemini-1.5-flash`

## Project Structure

```
├── app.py                  # LLM logic — Gemini client, chat with memory
├── api.py                  # FastAPI routes — /chat, /sessions
├── db.py                   # Supabase data layer
├── streamlit_app.py        # Streamlit UI
├── requirements.txt
├── .env                    # Environment variables (not committed)
└── supabase/
    └── migrations/         # SQL migration files
```

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

- **GOOGLE_API_KEY** — from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **SUPABASE_URL / SUPABASE_KEY** — from your Supabase project dashboard under *Settings → API*

### 3. Apply database migrations

Migrations are in `supabase/migrations/`. Apply them via the Supabase dashboard SQL editor or CLI:

```bash
supabase db push
```

Or apply each file manually in order.

## Running

Start the backend and frontend in separate terminals:

```bash
# Terminal 1 — Backend
uvicorn api:app --reload

# Terminal 2 — Frontend
streamlit run streamlit_app.py
```

The app will be available at `http://localhost:8501`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/chat` | Send a message |
| `GET` | `/sessions` | List all past sessions |
| `GET` | `/sessions/{session_id}` | Load a session with full history |

### POST `/chat` — Request body

```json
{
  "session_id": "uuid",
  "message": "Hello!",
  "model": "gemini-2.5-flash"
}
```

## Database Schema

```sql
sessions (id, session_id, current_model, created_at, updated_at)
messages (id, session_id, role, content, model, input_tokens, output_tokens, latency_ms, created_at)
```
