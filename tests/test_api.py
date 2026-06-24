from __future__ import annotations

import os
from importlib import reload
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

SAMPLE_DOC = """\
# FAQ

## Returns Policy
You can request a return within 30 days of purchase.
Contact our support team at support@example.com to initiate the process.

## Billing
If you see duplicate charges on your account, please attach your invoice
and screenshots when contacting billing@example.com.

## Pricing Plans
We offer three plans: Basic (free), Pro ($29/month), and Enterprise (custom pricing).
Annual subscribers receive a 20% discount on Pro and Enterprise plans.
"""


@pytest.fixture()
def client(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data" / "raw"
    models_dir = tmp_path / "models"
    data_dir.mkdir(parents=True)
    models_dir.mkdir(parents=True)
    (data_dir / "faq.md").write_text(SAMPLE_DOC, encoding="utf-8")

    # monkeypatch restores env vars automatically after the test
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("MODELS_DIR", str(models_dir))
    monkeypatch.setenv("INDEX_PATH", str(models_dir / "rag_index.joblib"))

    # Reload src.config first so INDEX_PATH/DATA_DIR pick up the new env vars,
    # then reload app.main so it re-imports the updated constants.
    import app.main as main_mod
    import src.config as config_mod

    reload(config_mod)  # must reload config before app.main so INDEX_PATH is updated
    reload(main_mod)
    with TestClient(main_mod.app) as c:
        yield c


# ── /health ──────────────────────────────────────────────────────────────────


class TestHealth:
    def test_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ── /index-info ───────────────────────────────────────────────────────────────


class TestIndexInfo:
    def test_not_loaded_before_ingest(self, client):
        r = client.get("/index-info")
        assert r.status_code == 200
        assert r.json()["loaded"] is False

    def test_loaded_after_ingest(self, client):
        client.post("/ingest")
        r = client.get("/index-info")
        body = r.json()
        assert body["loaded"] is True
        assert body["n_docs"] == 1
        assert body["n_chunks"] >= 1


# ── /ingest ───────────────────────────────────────────────────────────────────


class TestIngest:
    def test_returns_stats(self, client):
        r = client.post("/ingest")
        assert r.status_code == 200
        body = r.json()
        assert body["n_docs"] == 1
        assert body["n_chunks"] >= 1
        assert body["retriever_type"] == "tfidf"
        assert "created_at_utc" in body

    def test_blocked_without_api_key_when_configured(self, client):
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            r = client.post("/ingest")
        assert r.status_code == 401

    def test_accepted_with_valid_api_key(self, client):
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            r = client.post("/ingest", headers={"X-Api-Key": "secret123"})
        assert r.status_code == 200

    def test_rejected_with_wrong_api_key(self, client):
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            r = client.post("/ingest", headers={"X-Api-Key": "wrong-key"})
        assert r.status_code == 401


# ── /chat ─────────────────────────────────────────────────────────────────────


class TestChat:
    def test_503_when_no_index(self, client):
        r = client.post("/chat", json={"question": "What is the policy?"})
        assert r.status_code == 503

    def test_returns_answer_and_sources(self, client):
        client.post("/ingest")
        r = client.post("/chat", json={"question": "How many days to return?"})
        assert r.status_code == 200
        body = r.json()
        assert "answer" in body
        assert len(body["sources"]) >= 1

    def test_sources_have_required_fields(self, client):
        client.post("/ingest")
        r = client.post("/chat", json={"question": "Billing info?"})
        assert r.status_code == 200
        for src in r.json()["sources"]:
            assert {"source", "chunk_id", "score", "snippet"} <= src.keys()

    def test_question_too_short_is_422(self, client):
        client.post("/ingest")
        r = client.post("/chat", json={"question": "X"})
        assert r.status_code == 422

    def test_question_too_long_is_422(self, client):
        client.post("/ingest")
        r = client.post("/chat", json={"question": "A" * 501})
        assert r.status_code == 422

    def test_top_k_zero_is_422(self, client):
        client.post("/ingest")
        r = client.post("/chat", json={"question": "Returns?", "top_k": 0})
        assert r.status_code == 422

    def test_top_k_above_limit_is_422(self, client):
        client.post("/ingest")
        r = client.post("/chat", json={"question": "Returns?", "top_k": 21})
        assert r.status_code == 422

    def test_mode_is_extractive_without_anthropic_key(self, client, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        client.post("/ingest")
        r = client.post("/chat", json={"question": "What plans are available?"})
        assert r.status_code == 200
        assert r.json()["mode"] == "extractive"


# ── End-to-end ────────────────────────────────────────────────────────────────


class TestEndToEnd:
    def test_full_rag_pipeline(self, client, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        r = client.post("/ingest")
        assert r.status_code == 200
        assert r.json()["n_chunks"] >= 1

        r2 = client.post("/chat", json={"question": "How many days can I return an item?"})
        assert r2.status_code == 200
        body = r2.json()
        assert len(body["sources"]) >= 1
        assert body["sources"][0]["source"] == "faq.md"
        assert body["sources"][0]["score"] > 0
        assert body["mode"] == "extractive"
