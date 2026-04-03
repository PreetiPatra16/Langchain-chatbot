import os
from dotenv import load_dotenv
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

CHROMA_DIR = "./chroma_db"
COLLECTION = "mostlyai_docs"
DEFAULT_MODEL = "gemini-2.5-flash-lite"

# Some older Gemini 1.5 names are no longer available for generateContent
# on the current API version, so normalize them to a supported default.
MODEL_ALIASES = {
    "gemini-2.5-flash-lite": DEFAULT_MODEL,
}

# Shared embeddings + vectorstore (loaded once, reused across all chains)
_embeddings = None
_vectorstore = None


def normalize_model(model: str | None) -> str:
    model_name = (model or DEFAULT_MODEL).strip()
    return MODEL_ALIASES.get(model_name, model_name)


def _get_vectorstore():
    global _embeddings, _vectorstore
    if _vectorstore is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        _vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            collection_name=COLLECTION,
            embedding_function=_embeddings,
        )
    return _vectorstore


def build_chain(model: str = DEFAULT_MODEL):
    
    api_key = os.getenv("GOOGLE_API_KEY")
    model = normalize_model(model)

    retriever = _get_vectorstore().as_retriever(search_kwargs={"k": 4})

    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,
    )

    # Prompt to rewrite the user question given chat history
    condense_prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Given the conversation history and the latest user question, "
            "rewrite the question to be standalone (no pronouns referring to prior context). "
            "Return ONLY the rewritten question."
        )),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(llm, retriever, condense_prompt)

    # Prompt to answer strictly from retrieved context
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a helpful assistant for the MOSTLY AI documentation. "
            "Answer the question using ONLY the context below. "
            "If the answer is not in the context, say: "
            "'I don't have that information in the MOSTLY AI docs.'\n\n"
            "Context:\n{context}"
        )),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    chain = create_retrieval_chain(
        history_aware_retriever,
        create_stuff_documents_chain(llm, qa_prompt),
    )
    return chain


_chains_cache = {}

def get_chain(model: str = DEFAULT_MODEL):
    global _chains_cache
    model_norm = normalize_model(model)
    if model_norm not in _chains_cache:
        _chains_cache[model_norm] = build_chain(model_norm)
    return _chains_cache[model_norm]


def chat(user_input: str, chat_history: list, model: str = DEFAULT_MODEL) -> tuple[str, list, list]:
    """
    Send a message and get a response.

    Args:
        user_input: The user's message.
        chat_history: List of HumanMessage / AIMessage (last 10 = 5 turns).

    Returns:
        (answer, updated_chat_history, source_docs)
    """
    try:
        response = get_chain(model).invoke({
            "input": user_input,
            "chat_history": chat_history[-10:],
        })
    except Exception as e:
        # Retry once on connection timeouts/remote closed connection errors
        import time
        time.sleep(1)
        response = get_chain(model).invoke({
            "input": user_input,
            "chat_history": chat_history[-10:],
        })
    answer = response["answer"]
    source_docs = response.get("context", [])
    updated_history = chat_history + [
        HumanMessage(content=user_input),
        AIMessage(content=answer),
    ]
    return answer, updated_history, source_docs
