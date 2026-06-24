from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "data" / "raw")))
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(ROOT_DIR / "models")))
INDEX_PATH = Path(os.getenv("INDEX_PATH", str(MODELS_DIR / "rag_index.joblib")))

RETRIEVER = os.getenv("RETRIEVER", "tfidf").lower()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "120"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "30"))

TOP_K_DEFAULT = int(os.getenv("TOP_K_DEFAULT", "5"))
PORT = int(os.getenv("PORT", "8000"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
