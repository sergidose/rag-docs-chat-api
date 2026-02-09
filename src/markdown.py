from __future__ import annotations

import re
from typing import Any

_H2_RE = re.compile(r"(?m)^##\s+(.+?)\s*$")


def split_markdown_by_h2(text: str) -> list[dict[str, Any]]:
    """
    Divide un markdown por secciones H2 (##).
    Devuelve items con:
      - section: título sin ##
      - text_for_index: incluye el encabezado "## {section}" + body
    """
    matches = list(_H2_RE.finditer(text))
    if not matches:
        cleaned = text.strip()
        return [{"section": None, "text_for_index": cleaned}]

    out: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        section = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        text_for_index = f"## {section}\n{body}".strip()
        out.append({"section": section, "text_for_index": text_for_index})
    return out
