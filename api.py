from fastapi import FastAPI
from pydantic import BaseModel
from app import chat_with_memory
import db

app = FastAPI()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "gemini-2.5-flash"


@app.get("/")
def home():
    return {"message": "Chatbot API running"}


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return {"error": "Empty input"}

    result = chat_with_memory(req.session_id, req.message, req.model)

    if "error" in result:
        return result

    return {
        "session_id": req.session_id,
        "response": result["response"],
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "latency_ms": result["latency_ms"],
    }


@app.get("/sessions")
def sessions():
    return {"sessions": db.list_sessions()}


@app.get("/sessions/{session_id}")
def load_session(session_id: str):
    session = db.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    messages = db.get_history(session_id)
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
        return {"success": True, "message": "Session deleted"}
    except Exception as e:
        return {"error": str(e)}
