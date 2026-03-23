import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


def ensure_session(session_id: str, model: str) -> None:
    _supabase.table("sessions").upsert(
        {"session_id": session_id, "current_model": model},
        on_conflict="session_id",
    ).execute()


def update_session_model(session_id: str, model: str) -> None:
    _supabase.table("sessions").update(
        {"current_model": model}
    ).eq("session_id", session_id).execute()


def save_message(
    session_id: str,
    role: str,
    content: str,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    latency_ms: int | None = None,
) -> None:
    _supabase.table("messages").insert({
        "session_id": session_id,
        "role": role,
        "content": content,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
    }).execute()


def get_history(session_id: str) -> list[dict]:
    result = (
        _supabase.table("messages")
        .select("role, content, model, input_tokens, output_tokens, latency_ms, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data


def list_sessions() -> list[dict]:
    result = (
        _supabase.table("sessions")
        .select("session_id, current_model, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def get_session(session_id: str) -> dict | None:
    result = (
        _supabase.table("sessions")
        .select("session_id, current_model, created_at")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    return result.data


def delete_session(session_id: str) -> None:
    _supabase.table("messages").delete().eq("session_id", session_id).execute()
    _supabase.table("sessions").delete().eq("session_id", session_id).execute()
