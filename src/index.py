from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import joblib

from src.chunking import chunk_text
from src.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    INDEX_PATH,
    MODELS_DIR,
    RETRIEVER,
)
from src.docs import load_documents
from src.markdown import split_markdown_by_h2
from src.retriever import TfidfRetriever


def build_index(
    data_dir: str | Path,
    retriever_type: str = "tfidf",
    chunk_size: int = 200,
    overlap: int = 50,
) -> dict:
    """
    Construye índice:
    - carga docs
    - crea chunks
    - entrena retriever
    """
    data_dir = Path(data_dir)
    docs = load_documents(data_dir)

    chunks: list[dict] = []
    chunk_id = 0

    for d in docs:
        source = d["source"]
        text = d["text"]

        if str(source).lower().endswith(".md"):
            sections = split_markdown_by_h2(text)
        else:
            sections = [{"section": None, "text_for_index": text.strip()}]

        for s in sections:
            section_title = s["section"]
            section_text = s["text_for_index"]

            for c in chunk_text(section_text, chunk_size=chunk_size, overlap=overlap):
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "source": source,
                        "section": section_title,  # ✅ meta nueva
                        "text": c,  # ✅ incluye "## Planes" al inicio
                    }
                )
                chunk_id += 1

    texts = [c["text"] for c in chunks]

    if retriever_type != "tfidf":
        raise ValueError("Only retriever=tfidf is implemented in the base version.")

    retriever = TfidfRetriever()
    # Si no hay textos, construimos igualmente pero el chat devolverá 503 hasta ingestar docs
    if texts:
        retriever.build(texts)

    return {
        "retriever_type": retriever_type,
        "retriever": retriever,
        "chunks": chunks,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "n_docs": len(docs),
        "n_chunks": len(chunks),
    }


def save_index(index_obj: dict, index_path: str | Path) -> None:
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(index_obj, index_path)


def load_index(index_path: str | Path) -> dict:
    return joblib.load(index_path)


def build_and_save_index() -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    idx = build_index(
        DATA_DIR, retriever_type=RETRIEVER, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP
    )
    save_index(idx, INDEX_PATH)
    return idx


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default=str(DATA_DIR))
    p.add_argument("--index-path", default=str(INDEX_PATH))
    p.add_argument("--retriever", default=RETRIEVER)
    p.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    p.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    args = p.parse_args()

    idx = build_index(args.data_dir, args.retriever, args.chunk_size, args.overlap)
    save_index(idx, args.index_path)
    print(f"✅ Index saved to {args.index_path}")
    print(f"Docs: {idx['n_docs']} | Chunks: {idx['n_chunks']} | Retriever: {idx['retriever_type']}")


if __name__ == "__main__":
    main()
