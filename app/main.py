from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.auth import require_api_key
from src.config import CORS_ORIGINS, DATA_DIR, INDEX_PATH, TOP_K_DEFAULT
from src.index import build_index, load_index, save_index
from src.logger import get_logger
from src.rag import chat

log = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


class IngestOut(BaseModel):
    retriever_type: str
    n_docs: int
    n_chunks: int
    created_at_utc: str


class ChatIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)
    top_k: int = Field(default=TOP_K_DEFAULT, ge=1, le=20)


class Source(BaseModel):
    source: str
    section: str = ""
    chunk_id: int
    score: float
    snippet: str


class ChatOut(BaseModel):
    answer: str
    sources: list[Source]
    mode: str = "extractive"


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting RAG Docs Chat API")
    try:
        index_obj = load_index(INDEX_PATH)
        log.info(
            "Index loaded: %d docs, %d chunks",
            index_obj.get("n_docs", 0),
            index_obj.get("n_chunks", 0),
        )
    except FileNotFoundError:
        log.warning("No index found at %s — run POST /ingest to build it.", INDEX_PATH)
        index_obj = None

    app.state.index = index_obj
    yield
    log.info("Shutting down")
    app.state.index = None


app = FastAPI(
    title="RAG Docs Chat API",
    version="1.0.0",
    description=(
        "Answer questions about your documentation using TF-IDF retrieval "
        "with optional LLM-powered generation via Claude."
    ),
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/index-info", tags=["ops"])
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


@app.post(
    "/ingest",
    response_model=IngestOut,
    tags=["admin"],
    dependencies=[Depends(require_api_key)],
)
def ingest(request: Request) -> IngestOut:
    log.info("Ingesting documents from %s", DATA_DIR)
    idx = build_index(DATA_DIR)
    save_index(idx, INDEX_PATH)
    request.app.state.index = idx
    log.info("Ingest complete: %d docs, %d chunks", idx["n_docs"], idx["n_chunks"])
    return IngestOut(
        retriever_type=idx["retriever_type"],
        n_docs=idx["n_docs"],
        n_chunks=idx["n_chunks"],
        created_at_utc=idx["created_at_utc"],
    )


@app.post("/chat", response_model=ChatOut, tags=["chat"])
@limiter.limit("30/minute")
def chat_endpoint(request: Request, payload: ChatIn) -> ChatOut:
    idx = request.app.state.index
    if idx is None:
        raise HTTPException(status_code=503, detail="Index not loaded. Run POST /ingest first.")
    log.info("Chat query (top_k=%d): %.80s", payload.top_k, payload.question)
    result = chat(idx, payload.question, top_k=payload.top_k)
    return ChatOut(
        answer=result["answer"],
        sources=result["sources"],
        mode=result.get("mode", "extractive"),
    )
