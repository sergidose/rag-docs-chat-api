from __future__ import annotations

import logging
import re
from typing import Any

from src.config import TOP_K_DEFAULT
from src.llm import generate_answer

log = logging.getLogger(__name__)

_H2_ANY_RE = re.compile(r"^\s*##\s+([^\n\r]+?)(?:\r?\n|\s+)", re.UNICODE)


def strip_leading_h2(text: str) -> str:
    t = (text or "").strip()
    return _H2_ANY_RE.sub("", t, count=1).strip()


def short_answer(text: str, max_chars: int = 320) -> str:
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]
    clean = " ".join(lines).strip()
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    out = " ".join(sentences[:2]).strip()
    return (out[:max_chars] + "…") if len(out) > max_chars else out


def _to_list(x: Any) -> list:
    if x is None:
        return []
    if hasattr(x, "tolist"):
        return x.tolist()
    return list(x)


def chat(index_obj: dict, question: str, top_k: int = TOP_K_DEFAULT) -> dict[str, Any]:
    retriever = index_obj["retriever"]
    chunks = index_obj["chunks"]

    if not chunks:
        return {
            "answer": "No documents indexed yet. Run POST /ingest first.",
            "sources": [],
            "mode": "none",
        }

    top_k = max(1, min(int(top_k), len(chunks)))
    idxs, scores = retriever.query(question, k=top_k)

    idx_list = _to_list(idxs)
    score_list = _to_list(scores)

    sources: list[dict[str, Any]] = []
    top_chunks: list[dict] = []
    for i, score in zip(idx_list, score_list, strict=False):
        c = chunks[i]
        sources.append(
            {
                "source": c.get("source", ""),
                "section": c.get("section") or "",
                "chunk_id": c.get("chunk_id", 0),
                "score": float(score),
                "snippet": c["text"][:240] + ("…" if len(c["text"]) > 240 else ""),
            }
        )
        top_chunks.append(c)

    log.debug("Retrieved %d chunks for question: %.60s…", len(top_chunks), question)

    answer = generate_answer(question, top_chunks)
    if answer is not None:
        mode = "llm"
        log.debug("LLM answer used")
    else:
        top_text = chunks[idx_list[0]]["text"] if idx_list else ""
        answer = short_answer(strip_leading_h2(top_text))
        mode = "extractive"
        log.debug("Extractive fallback used")

    return {"answer": answer, "sources": sources, "mode": mode}
