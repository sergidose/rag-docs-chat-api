from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfRetriever:
    """
    Retriever clásico TF-IDF (ligero, reproducible, perfecto para CI/Docker).
    """

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=50_000,
            norm="l2",
        )
        self.matrix = None  # sparse

    def build(self, texts: list[str]) -> None:
        self.matrix = self.vectorizer.fit_transform(texts)

    def query(self, query_text: str, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
        if self.matrix is None:
            raise RuntimeError("Retriever not built. Call build() first.")

        q = self.vectorizer.transform([query_text])
        scores = (self.matrix @ q.T).toarray().ravel()  # dot ≈ cosine (por L2 norm)
        idx = np.argsort(scores)[::-1][:k]
        return idx, scores[idx]
