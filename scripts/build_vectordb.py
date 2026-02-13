"""
Build ChromaDB from processed chunks using Gemini embeddings.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def batched(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def embed_documents(texts: list[str], model: str) -> list[list[float]]:
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = genai.embed_content(
                model=model,
                content=texts,
                task_type="retrieval_document",
            )
            embeddings = response.get("embedding")
            if not embeddings:
                raise RuntimeError("Gemini embedding 응답이 비어 있습니다.")
            return embeddings
        except Exception as exc:  # pragma: no cover
            last_error = exc
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"임베딩 실패: {last_error}")


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY가 없습니다.")

    genai.configure(api_key=api_key)

    chunks_path = Path(os.getenv("PROCESSED_CHUNKS_PATH", "./data/processed/chunks.jsonl"))
    chroma_dir = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/vectordb"))
    embedding_model = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

    if not chunks_path.exists():
        raise SystemExit(f"Missing processed chunks: {chunks_path}")

    rows: list[dict] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    if not rows:
        raise SystemExit("No chunks to ingest")

    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = chroma_client.get_or_create_collection(
        name="msk_knowledge_base", metadata={"hnsw:space": "cosine"}
    )

    batch_size = 32
    total = 0
    for batch in batched(rows, batch_size):
        texts = [r["text"] for r in batch]
        ids = [r["id"] for r in batch]
        metadatas = [{"source": r["source"], "page": r["page"]} for r in batch]

        vectors = embed_documents(texts, embedding_model)

        collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=vectors)
        total += len(batch)
        print(f"Upserted {total}/{len(rows)}")

    print(f"Done. Collection count: {collection.count()}")


if __name__ == "__main__":
    main()
