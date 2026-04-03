import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


def ensure_session(session_id: str, model: str) -> None:
    try:
        _supabase.table("sessions").upsert(
            {"session_id": session_id, "current_model": model},
            on_conflict="session_id",
        ).execute()
    except Exception as e:
        print(f"ensure_session error: {e}")


def update_session_model(session_id: str, model: str) -> None:
    try:
        _supabase.table("sessions").update(
            {"current_model": model}
        ).eq("session_id", session_id).execute()
    except Exception as e:
        print(f"update_session_model error: {e}")


def save_message(
    session_id: str,
    role: str,
    content: str,
    sources: list[str] | None = None,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    latency_ms: int | None = None,
) -> None:
    try:
        _supabase.table("messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
        }).execute()
    except Exception as e:
        print(f"save_message error: {e}")


def get_history(session_id: str, limit: int = 10) -> list[dict]:
    try:
        result = (
            _supabase.table("messages")
            .select("role, content, sources, model, input_tokens, output_tokens, latency_ms, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(result.data))  # chronological order for LangChain
    except Exception as e:
        print(f"get_history error: {e}")
        return []


def list_sessions() -> list[dict]:
    try:
        result = (
            _supabase.table("sessions")
            .select("session_id, current_model, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"list_sessions error: {e}")
        return []


def get_session(session_id: str) -> dict | None:
    try:
        result = (
            _supabase.table("sessions")
            .select("session_id, current_model, created_at")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"get_session error: {e}")
        return None


def delete_session(session_id: str) -> None:
    try:
        # Use an RPC for transactional guarantees and isolation.
        _supabase.rpc("delete_session_rpc", {"p_session_id": session_id}).execute()
    except Exception as e:
        # Fallback if RPC is not present or failed, executing non-isolated deletes
        print(f"delete_session RPC error: {e}. Falling back to sequential deletion.")
        try:
            _supabase.table("messages").delete().eq("session_id", session_id).execute()
            _supabase.table("sessions").delete().eq("session_id", session_id).execute()
        except Exception as inner_e:
            print(f"delete_session error: {inner_e}")
