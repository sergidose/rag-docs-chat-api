from __future__ import annotations

import re
from typing import Any

from src.config import TOP_K_DEFAULT


_H2_ANY_RE = re.compile(r"^\s*##\s+([^\n\r]+?)(?:\r?\n|\s+)", re.UNICODE)


def strip_leading_h2(text: str) -> str:
    t = (text or "").strip()
    return _H2_ANY_RE.sub("", t, count=1).strip()


def split_markdown_by_h2(md: str) -> list[tuple[str, str]]:
    """
    Devuelve lista de (titulo, contenido) para cada sección '## ...'.

    - Si no hay '##', devuelve una sola sección ("document", md).
    - Si hay texto antes del primer '##', se devuelve como ("intro", pre).
    """
    md = md.strip()

    # Divide manteniendo los títulos de nivel ## como separadores.
    # parts[0] => texto antes del primer "##" (si existe)
    # parts[1:] => bloques que empiezan con "Titulo\\ncontenido..."
    parts = re.split(r"(?m)^##\s+", md)

    if len(parts) == 1:
        return [("document", md)]

    sections: list[tuple[str, str]] = []

    pre = parts[0].strip()
    if pre:
        sections.append(("intro", pre))

    for block in parts[1:]:
        lines = block.splitlines()
        title = lines[0].strip() if lines else "untitled"
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        sections.append((title, body))

    return sections


def short_answer(text: str, max_chars: int = 320) -> str:
    """
    Devuelve una respuesta corta (1–2 frases) a partir del chunk recuperado.
    Quita headers markdown y recorta.
    """
    # Quitar headers markdown tipo # / ## / ### ...
    lines = [line for line in text.splitlines() if not line.strip().startswith("#")]

    clean = " ".join(lines).strip()

    # 1–2 frases
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    out = " ".join(sentences[:2]).strip()

    return (out[:max_chars] + "…") if len(out) > max_chars else out


def _to_list(x: Any) -> list:
    """Convierte arrays (numpy) o iterables a list de forma segura."""
    if x is None:
        return []
    if hasattr(x, "tolist"):
        return x.tolist()
    return list(x)


def chat(index_obj: dict, question: str, top_k: int = TOP_K_DEFAULT) -> dict[str, Any]:
    """
    “Chat” extractivo:
    - Recupera top_k chunks por similitud
    - Responde con un resumen corto del chunk top1
    - Devuelve fuentes (sources) con snippet
    """
    retriever = index_obj["retriever"]
    chunks = index_obj["chunks"]

    if not chunks:
        return {
            "answer": "No hay documentos indexados todavía. Ejecuta POST /ingest para crear el índice.",
            "sources": [],
        }

    top_k = max(1, min(int(top_k), len(chunks)))
    idxs, scores = retriever.query(question, k=top_k)

    idx_list = _to_list(idxs)
    score_list = _to_list(scores)

    sources: list[dict[str, Any]] = []
    for i, score in zip(idx_list, score_list):
        c = chunks[i]
        sources.append(
            {
                "source": c.get("source", ""),
                # si tu pipeline de ingest crea 'section', lo verás aquí
                "section": c.get("section", ""),
                "chunk_id": c.get("chunk_id", 0),
                "score": float(score),
                "snippet": c["text"][:240] + ("…" if len(c["text"]) > 240 else ""),
            }
        )

    top_text = chunks[idx_list[0]]["text"] if idx_list else ""
    print("DEBUG top_text[:200] =", repr(top_text[:200]))
    print("DEBUG stripped[:200]  =", repr(strip_leading_h2(top_text)[:200]))

    answer_text = short_answer(strip_leading_h2(top_text))
    print("DEBUG answer_text =", repr(answer_text))

    # Respuesta sin volcar el documento entero
    answer = f"Respuesta (modo extractivo):\n{answer_text}\n\nFuentes: ver 'sources'."

    return {"answer": answer, "sources": sources}
