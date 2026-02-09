from pathlib import Path

from src.config import DATA_DIR, INDEX_PATH, RETRIEVER


def test_sanity_config():
    assert RETRIEVER == "tfidf"

    # Cross-platform: acepta data/raw tanto en Windows como Linux
    assert Path(DATA_DIR).parts[-2:] == ("data", "raw")

    assert Path(INDEX_PATH).parts[-2:] == ("models", "rag_index.joblib")
