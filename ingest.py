import json
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

CHROMA_DIR = "./chroma_db"
COLLECTION = "mostlyai_docs"


def load_pages(path: str = "pages.json") -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []


def build_documents(pages: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    docs = []
    for page in pages:
        markdown_text = page.get("markdown", "")
        if not markdown_text:
            continue
        chunks = splitter.create_documents(
            texts=[markdown_text],
            metadatas=[{"source": page.get("url", ""), "title": page.get("title", "")}],
        )
        docs.extend(chunks)
    return docs


def main():
    print("Loading pages...")
    pages = load_pages()
    print(f"  {len(pages)} pages loaded")

    print("Chunking...")
    docs = build_documents(pages)
    print(f"  {len(docs)} chunks created")

    print("Embedding and persisting to ChromaDB...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    ids = [hashlib.md5((doc.metadata.get("source", "") + doc.page_content).encode("utf-8")).hexdigest() for doc in docs]
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        ids=ids,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION,
    )
    print(f"Done. Vector store saved to {CHROMA_DIR}/")


if __name__ == "__main__":
    main()
