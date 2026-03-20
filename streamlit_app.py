import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

st.title("💬 AI Chatbot ")

# Unique session per user
if "session_id" not in st.session_state:
    st.session_state.session_id = "user1"

# Store messages locally for UI
if "messages" not in st.session_state:
    st.session_state.messages = []

# Input box
user_input = st.text_input("You:")

if st.button("Send"):
    if user_input.strip():
        response = requests.post(
            API_URL,
            json={
                "session_id": st.session_state.session_id,
                "message": user_input
            }
        )

        data = response.json()
        bot_reply = data.get("response", "Error")

        # Save messages
        st.session_state.messages.append(("You", user_input))
        st.session_state.messages.append(("Bot", bot_reply))

# Display chat
for sender, msg in st.session_state.messages:
    if sender == "You":
        st.write(f" **You:** {msg}")
    else:
        st.write(f" **Bot:** {msg}")