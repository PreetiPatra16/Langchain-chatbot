import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

import db
from rag import chat as rag_chat, get_chain, normalize_model

# Cap concurrent RAG calls to protect the embedding model and ChromaDB
# under ~200 concurrent users; excess requests queue behind the semaphore
_semaphore = asyncio.Semaphore(20)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up default chain at startup so the first request isn't slow
    get_chain()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "gemini-2.0-flash"


@app.get("/")
def home():
    return {"message": "RAG Chatbot API running"}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        return {"error": "Empty input"}

    model = normalize_model(req.model)
    db.ensure_session(req.session_id, model)

    # Fetch last 10 messages (5 turns) for RAG context
    history_rows = db.get_history(req.session_id, limit=10)
    chat_history = []
    for row in history_rows:
        if row["role"] == "user":
            chat_history.append(HumanMessage(content=row["content"]))
        else:
            chat_history.append(AIMessage(content=row["content"]))

    t0 = time.time()

    # Offload blocking LangChain call to thread pool; semaphore prevents overload
    loop = asyncio.get_event_loop()
    async with _semaphore:
        answer, _, source_docs = await loop.run_in_executor(
            None, rag_chat, req.message, chat_history, model
        )

    latency_ms = int((time.time() - t0) * 1000)

    sources = list(dict.fromkeys(
        doc.metadata.get("source", "") for doc in source_docs
        if doc.metadata.get("source")
    ))

    db.save_message(req.session_id, "user", req.message)
    db.save_message(
        req.session_id, "assistant", answer,
        sources=sources or None,
        model=model,
        latency_ms=latency_ms,
    )

    return {
        "session_id": req.session_id,
        "response": answer,
        "sources": sources,
        "model": model,
        "latency_ms": latency_ms,
    }


@app.get("/sessions")
def sessions():
    return {"sessions": db.list_sessions()}


@app.get("/sessions/{session_id}")
def load_session(session_id: str):
    session = db.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    messages = db.get_history(session_id, limit=50)
    return {
        "session_id": session_id,
        "current_model": session["current_model"],
        "created_at": session["created_at"],
        "messages": messages,
    }


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    try:
        db.delete_session(session_id)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}
