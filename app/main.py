from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from src.config import DATA_DIR, INDEX_PATH, TOP_K_DEFAULT
from src.index import build_index, load_index, save_index
from src.rag import chat


class IngestOut(BaseModel):
    retriever_type: str
    n_docs: int
    n_chunks: int
    created_at_utc: str


class ChatIn(BaseModel):
    question: str = Field(..., min_length=2)
    top_k: int = Field(default=TOP_K_DEFAULT, ge=1, le=20)


class Source(BaseModel):
    source: str
    chunk_id: int
    score: float
    snippet: str


class ChatOut(BaseModel):
    answer: str
    sources: list[Source]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        index_obj = load_index(INDEX_PATH)
    except FileNotFoundError:
        index_obj = None

    app.state.index = index_obj
    yield
    app.state.index = None


app = FastAPI(title="RAG Docs Chat API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/index-info")
def index_info(request: Request) -> dict[str, Any]:
    idx = request.app.state.index
    if idx is None:
        return {"loaded": False, "index_path": str(INDEX_PATH)}
    return {
        "loaded": True,
        "index_path": str(INDEX_PATH),
        "retriever_type": idx.get("retriever_type"),
        "n_docs": idx.get("n_docs"),
        "n_chunks": idx.get("n_chunks"),
        "created_at_utc": idx.get("created_at_utc"),
    }


@app.post("/ingest", response_model=IngestOut)
def ingest(request: Request) -> IngestOut:
    idx = build_index(DATA_DIR)
    save_index(idx, INDEX_PATH)
    request.app.state.index = idx
    return IngestOut(
        retriever_type=idx["retriever_type"],
        n_docs=idx["n_docs"],
        n_chunks=idx["n_chunks"],
        created_at_utc=idx["created_at_utc"],
    )


@app.post("/chat", response_model=ChatOut)
def chat_endpoint(payload: ChatIn, request: Request) -> ChatOut:
    idx = request.app.state.index
    if idx is None:
        raise HTTPException(
            status_code=503, detail="Index not loaded. Run POST /ingest first."
        )
    result = chat(idx, payload.question, top_k=payload.top_k)
    return ChatOut(**result)
