import os
from dotenv import load_dotenv
from google import genai

# ------------------ LOAD ENV ------------------
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

# ------------------ GEMINI CLIENT ------------------
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

# ------------------ MEMORY ------------------
# Stores chat history for multiple users
chat_sessions = {}

def chat_with_memory(session_id, user_input):
    if not client:
        return "Error: API key not configured"

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id]

    # Convert history to text
    history_text = "\n".join(history)

    # Final prompt
    final_prompt = f"""
    You are a helpful assistant.

    Conversation so far:
    {history_text}

    User: {user_input}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt
        )

        answer = response.text

        # Save history
        history.append(f"User: {user_input}")
        history.append(f"Bot: {answer}")

        return answer

    except Exception as e:
        return f"Error: {str(e)}"