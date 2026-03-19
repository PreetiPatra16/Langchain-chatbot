from fastapi import FastAPI
from pydantic import BaseModel
from app import chat_with_memory

app = FastAPI()

# Request format
class ChatRequest(BaseModel):
    session_id: str
    message: str

# Health check
@app.get("/")
def home():
    return {"message": "Chatbot API running"}

# Chat endpoint
@app.post("/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        return {"error": "Empty input"}

    response = chat_with_memory(req.session_id, req.message)

    return {
        "session_id": req.session_id,
        "response": response
    }