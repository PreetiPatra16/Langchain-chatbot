import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

CHROMA_DIR = "./chroma_db"
COLLECTION = "mostlyai_docs"


def load_pages(path: str = "pages.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_documents(pages: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    docs = []
    for page in pages:
        chunks = splitter.create_documents(
            texts=[page["markdown"]],
            metadatas=[{"source": page["url"], "title": page.get("title", "")}],
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
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION,
    )
    print(f"Done. Vector store saved to {CHROMA_DIR}/")


if __name__ == "__main__":
    main()
