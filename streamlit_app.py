import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8000/chat"
SESSIONS_URL = "http://127.0.0.1:8000/sessions"

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

# ── Session state init ──────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = GEMINI_MODELS[0]

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Model")
    selected = st.selectbox(
        "Select Gemini model",
        GEMINI_MODELS,
        index=GEMINI_MODELS.index(st.session_state.selected_model),
        label_visibility="collapsed",
    )
    if selected != st.session_state.selected_model:
        st.session_state.selected_model = selected

    st.divider()
    st.header("Sessions")

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        if st.button("✨ New Session", use_container_width=True, key="new_session_btn"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.selected_model = GEMINI_MODELS[0]
            st.rerun()
    with col2:
        st.write("")  # Spacing

    try:
        resp = requests.get(SESSIONS_URL, timeout=3)
        past_sessions = resp.json().get("sessions", [])
    except Exception:
        past_sessions = []

    if past_sessions:
        st.caption(f"📋 {len(past_sessions)} saved session(s)")

    for s in past_sessions:
        sid = s["session_id"]
        date = s["created_at"][:10]
        model_label = s["current_model"].replace("gemini-", "")
        is_active = sid == st.session_state.session_id
        
        col_session, col_delete = st.columns([0.85, 0.15])
        
        with col_session:
            session_label = f"📌 {sid[:8]}…  {date}  [{model_label}]"
            if st.button(
                session_label,
                key=f"session_{sid}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                try:
                    detail = requests.get(f"{SESSIONS_URL}/{sid}", timeout=3).json()
                    st.session_state.session_id = sid
                    st.session_state.selected_model = detail.get("current_model", GEMINI_MODELS[0])
                    st.session_state.messages = [
                        ("You" if m["role"] == "user" else "Bot", m["content"])
                        for m in detail.get("messages", [])
                    ]
                    st.rerun()
                except Exception:
                    st.error("Failed to load session.")
        
        with col_delete:
            if st.button("🗑️", key=f"delete_{sid}", help="Delete this session", type="secondary"):
                try:
                    requests.delete(f"{SESSIONS_URL}/{sid}", timeout=3)
                    st.success("Session deleted!", icon="✓")
                    if st.session_state.session_id == sid:
                        st.session_state.session_id = str(uuid.uuid4())
                        st.session_state.messages = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete session: {str(e)}")

# ── Main chat ────────────────────────────────────────────────────────────────
st.title("💬 AI Chatbot")
st.caption(f"Session: `{st.session_state.session_id[:8]}…`  ·  Model: `{st.session_state.selected_model}`")

for sender, msg in st.session_state.messages:
    with st.chat_message("user" if sender == "You" else "assistant"):
        st.write(msg)

user_input = st.chat_input("Message…")

if user_input and user_input.strip():
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "session_id": st.session_state.session_id,
                        "message": user_input,
                        "model": st.session_state.selected_model,
                    },
                    timeout=60,
                )
                data = response.json()
            except Exception as e:
                data = {"error": str(e)}

        if "error" in data:
            st.error(data["error"])
        else:
            bot_reply = data["response"]
            st.write(bot_reply)
            st.caption(
                f"Model: `{data.get('model', '—')}`  ·  "
                f"Tokens in/out: {data.get('input_tokens', '?')}/{data.get('output_tokens', '?')}  ·  "
                f"Latency: {data.get('latency_ms', '?')} ms"
            )
            st.session_state.messages.append(("You", user_input))
            st.session_state.messages.append(("Bot", bot_reply))
