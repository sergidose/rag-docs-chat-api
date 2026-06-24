from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based exclusively on "
    "the provided documentation context. Be concise and accurate. "
    "If the context does not contain enough information, state that clearly "
    "instead of making up information."
)


def build_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for c in chunks:
        source = c.get("source", "unknown")
        section = c.get("section") or ""
        label = f"{source} › {section}" if section else source
        parts.append(f"[{label}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def generate_answer(question: str, chunks: list[dict[str, Any]]) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        context = build_context(chunks)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (f"Documentation:\n\n{context}\n\n---\n\nQuestion: {question}"),
                }
            ],
        )
        answer: str = message.content[0].text
        log.debug("LLM answer generated (%d chars)", len(answer))
        return answer
    except Exception as exc:
        log.warning("LLM generation failed, using extractive fallback: %s", exc)
        return None
