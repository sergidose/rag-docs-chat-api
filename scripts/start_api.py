from __future__ import annotations

import os

import uvicorn

from src.config import INDEX_PATH, PORT
from src.index import build_and_save_index


def main() -> None:
    # Demo reproducible: si no hay índice, lo generamos automáticamente
    if not INDEX_PATH.exists():
        print("ℹ️  Index not found. Building index from data/raw...")
        idx = build_and_save_index()
        print(f"✅ Built index. Chunks: {idx['n_chunks']}")

    port = int(os.getenv("PORT", str(PORT)))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
