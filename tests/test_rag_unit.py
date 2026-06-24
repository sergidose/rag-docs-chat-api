from __future__ import annotations

from src.rag import chat, short_answer, strip_leading_h2

# ── strip_leading_h2 ─────────────────────────────────────────────────────────


def test_strip_h2_removes_header():
    text = "## Returns Policy\nYou can return within 30 days."
    result = strip_leading_h2(text)
    assert "##" not in result
    assert "Returns Policy" not in result
    assert "30 days" in result


def test_strip_h2_is_noop_without_header():
    text = "Just plain text without any markdown header."
    assert strip_leading_h2(text) == text


def test_strip_h2_handles_empty_string():
    assert strip_leading_h2("") == ""
    assert strip_leading_h2("   ") == ""


# ── short_answer ─────────────────────────────────────────────────────────────


def test_short_answer_truncates_at_max_chars():
    # Two real sentences whose combined length clearly exceeds max_chars=30
    text = (
        "This is a fairly long first sentence that contains many words. "
        "This is also a fairly long second sentence with additional info."
    )
    result = short_answer(text, max_chars=30)
    assert result.endswith("…")
    assert len(result) <= 31  # max_chars + "…"


def test_short_answer_strips_markdown_headers():
    text = "# Big Title\n## Sub Title\nActual content follows here."
    result = short_answer(text)
    assert "#" not in result
    assert "Actual content" in result


def test_short_answer_returns_at_most_two_sentences():
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    result = short_answer(text)
    assert "Third sentence" not in result
    assert "Fourth sentence" not in result


def test_short_answer_handles_empty():
    assert short_answer("") == ""


# ── chat ─────────────────────────────────────────────────────────────────────


def test_chat_empty_chunks_returns_ingest_message():
    fake_index = {"retriever": None, "chunks": []}
    result = chat(fake_index, "What is the policy?")
    assert "ingest" in result["answer"].lower()
    assert result["sources"] == []
    assert result["mode"] == "none"


def test_chat_extractive_mode_without_api_key(index_obj, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = chat(index_obj, "What is the returns policy?")
    assert "answer" in result
    assert len(result["sources"]) >= 1
    assert result["mode"] == "extractive"
    assert result["sources"][0]["score"] > 0


def test_chat_sources_contain_required_fields(index_obj, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = chat(index_obj, "Billing info?")
    for src in result["sources"]:
        assert "source" in src
        assert "chunk_id" in src
        assert "score" in src
        assert "snippet" in src


def test_chat_top_k_limits_sources(index_obj, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = chat(index_obj, "What plans are available?", top_k=2)
    assert len(result["sources"]) <= 2


def test_chat_snippet_is_truncated(index_obj, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = chat(index_obj, "Returns?")
    for src in result["sources"]:
        assert len(src["snippet"]) <= 241  # 240 chars + optional "…"
