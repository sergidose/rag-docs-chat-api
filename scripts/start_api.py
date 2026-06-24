from __future__ import annotations

import os

import uvicorn

from src.config import INDEX_PATH, PORT
from src.index import build_and_save_index
from src.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    if not INDEX_PATH.exists():
        log.info("No index found. Building from data/raw …")
        idx = build_and_save_index()
        log.info("Index built: %d chunks from %d docs", idx["n_chunks"], idx["n_docs"])

    port = int(os.getenv("PORT", str(PORT)))
    log.info("Starting API on port %d", port)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
