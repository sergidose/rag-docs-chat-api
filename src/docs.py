from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTS = {".md", ".txt"}


def iter_doc_paths(data_dir: Path) -> list[Path]:
    """Lista docs soportados dentro de data_dir (recursivo)."""
    if not data_dir.exists():
        return []
    paths: list[Path] = []
    for p in data_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            paths.append(p)
    return sorted(paths)


def read_text(path: Path) -> str:
    """Lee texto UTF-8 (tolerante a errores)."""
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def load_documents(data_dir: Path) -> list[dict]:
    """
    Devuelve:
    [{ "source": "<filename>", "text": "<full text>" }, ...]
    """
    docs: list[dict] = []
    for p in iter_doc_paths(data_dir):
        txt = read_text(p)
        if txt:
            docs.append({"source": p.name, "text": txt})
    return docs
