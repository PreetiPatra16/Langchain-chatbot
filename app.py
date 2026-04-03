import os
import streamlit as st
from rag import chat
from db import _supabase

st.set_page_config(page_title="MOSTLY AI Docs Assistant", page_icon="🤖")

def login_or_signup():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is not None:
        return True

    st.title("Welcome to MOSTLY AI Docs Assistant")
    
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        st.subheader("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                response = _supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                if response.user:
                    st.session_state.user = response.user
                    st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
                
    with tab2:
        st.subheader("Create Account")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            try:
                response = _supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                if response.user:
                    # Automatically log the user in
                    st.session_state.user = response.user
                    st.rerun()
                else:
                    st.success("Registration successful! Please check your email for a confirmation link.")
            except Exception as e:
                st.error(f"Sign up failed: {str(e)}")

    return False

if not login_or_signup():
    st.stop()

import uuid

# --- Sidebar logic ---
st.sidebar.markdown(f"👤 **{st.session_state.user.email}**")
if st.sidebar.button("Sign Out"):
    st.session_state.user = None
    if "sessions" in st.session_state:
        del st.session_state.sessions
    if "active_session_id" in st.session_state:
        del st.session_state.active_session_id
    st.rerun()

st.sidebar.divider()

if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

def create_new_session():
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {
        "title": f"Chat {len(st.session_state.sessions) + 1}",
        "messages": [],
        "chat_history": []
    }
    st.session_state.active_session_id = new_id

if not st.session_state.sessions or st.session_state.active_session_id is None:
    create_new_session()

if st.sidebar.button("➕ New Chat"):
    create_new_session()
    st.rerun()

st.sidebar.subheader("Recent Chats")
for sess_id, sess_data in st.session_state.sessions.items():
    label = sess_data["title"]
    # Provide visual indication of active chat
    if sess_id == st.session_state.active_session_id:
        label = f"💬 {label}"
    else:
        label = f"📁 {label}"
    if st.sidebar.button(label, key=f"btn_{sess_id}"):
        st.session_state.active_session_id = sess_id
        st.rerun()

# --- Main App ---
st.title("MOSTLY AI Docs Assistant")
st.caption("Ask anything about MOSTLY AI — answers are grounded in the official documentation.")

active_session = st.session_state.sessions[st.session_state.active_session_id]

# Render existing messages
for msg in active_session["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for src in msg["sources"]:
                    st.markdown(f"- [{src}]({src})")

# Chat input
if user_input := st.chat_input("Ask about MOSTLY AI..."):
    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    active_session["messages"].append({"role": "user", "content": user_input})

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, updated_history, source_docs = chat(
                    user_input, active_session["chat_history"]
                )
            except Exception as e:
                active_session["messages"].pop()
                st.error(f"Error communicating with AI: {str(e)}\nPlease try asking your question again.")
                st.stop()
                
        st.markdown(answer)

        # Deduplicate source URLs
        sources = list(dict.fromkeys(
            doc.metadata.get("source", "") for doc in source_docs
            if doc.metadata.get("source")
        ))
        if sources:
            with st.expander("Sources"):
                for src in sources:
                    st.markdown(f"- [{src}]({src})")

    active_session["chat_history"] = updated_history[-10:]  # keep last 5 turns
    active_session["messages"].append({
        "role": "assistant",
        "content": answer,
        "sources": sources if sources else [],
    })
    
    st.rerun()
