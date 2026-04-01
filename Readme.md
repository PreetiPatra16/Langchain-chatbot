# MOSTLY AI Docs RAG Chatbot

A RAG chatbot that answers questions grounded in the [MOSTLY AI documentation](https://docs.mostly.ai/), with a FastAPI backend supporting ~200 anonymous concurrent users and Supabase-persisted sessions.

**Stack:** Crawl4AI · LangChain · ChromaDB · HuggingFace Embeddings · Gemini · FastAPI · Supabase · Streamlit

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
GOOGLE_API_KEY=your_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key
```

## Build the Knowledge Base

Run these once to populate ChromaDB:

```bash
python scrape.py   # crawls docs.mostly.ai → pages.json
python ingest.py   # chunks + embeds → chroma_db/
```

## Running

### API (FastAPI)

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1
```

> Use `--workers 1` — the embedding model singleton must not be forked across processes.

Interactive docs available at `http://localhost:8000/docs`.

### UI (Streamlit)

```bash
streamlit run app.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a message, get a RAG-grounded response |
| `GET` | `/sessions` | List all sessions |
| `GET` | `/sessions/{session_id}` | Load session history |
| `DELETE` | `/sessions/{session_id}` | Delete a session |

### Example `/chat` request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What is MOSTLY AI?",
    "model": "gemini-2.0-flash"
  }'
```

The `session_id` is a client-generated UUID. The server creates the session on first use — no prior registration needed.

## Architecture

- **Anonymous sessions** — client generates a UUID and sends it with each request; no auth required
- **Persistent history** — last 50 messages per session stored in Supabase; only last 10 fetched for RAG context
- **Concurrency control** — semaphore caps at 20 concurrent RAG calls; remaining requests queue safely
- **Single process** — embeddings and ChromaDB loaded once at startup, shared across all requests via thread pool

## Database Migrations

Migration files are in `supabase/migrations/`. Apply them via the Supabase dashboard SQL editor or CLI:

```bash
supabase db push
```

## Notes

- Embeddings use `BAAI/bge-small-en-v1.5` locally (no API quota limits)
- Model is configurable per request (defaults to `gemini-2.0-flash`)
- Re-run `scrape.py` + `ingest.py` (after `rm -rf chroma_db/`) to refresh docs
