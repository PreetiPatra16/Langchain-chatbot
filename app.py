import os
import time
from dotenv import load_dotenv
from google import genai
import db

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def chat_with_memory(session_id: str, user_input: str, model: str) -> dict:
    if not client:
        return {"error": "API key not configured"}

    db.ensure_session(session_id, model)

    history = db.get_history(session_id)
    history_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Bot'}: {m['content']}"
        for m in history
    )

    final_prompt = f"""You are a helpful assistant.

Conversation so far:
{history_text}

User: {user_input}"""

    db.save_message(session_id, "user", user_input)

    try:
        t0 = time.time()
        response = client.models.generate_content(
            model=model,
            contents=final_prompt,
        )
        latency_ms = int((time.time() - t0) * 1000)

        answer = response.text
        usage = response.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)

        db.save_message(
            session_id, "assistant", answer,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )

        return {
            "response": answer,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        return {"error": str(e)}
