import os
from dotenv import load_dotenv
from google import genai
from langchain_core.prompts import PromptTemplate

# Loading variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key missing")

# Initializing Gemini client
client = genai.Client(api_key=api_key)


prompt = PromptTemplate(
    input_variables=["question"],
    template="You are a helpful assistant. Answer clearly:\n{question}"
)

print("Chatbot started! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    if not user_input.strip():
        print("Please enter a valid question.")
        continue

    try:
        final_prompt = prompt.format(question=user_input)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt
        )

        print("Chatbot:", response.text)

    except Exception as e:
        print("Error:", str(e))

        result = response.json()

        if "candidates" in result:
            answer = result["candidates"][0]["content"]["parts"][0]["text"]
            print("Chatbot:", answer)
        else:
            print("Error from API:", result)

    except Exception as e:
        print("Error:", str(e))