from __future__ import annotations

from src.chunking import chunk_text


def test_empty_input_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_text_shorter_than_chunk_is_single_chunk():
    text = " ".join(["word"] * 10)
    chunks = chunk_text(text, chunk_size=20, overlap=0)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_count_with_no_overlap():
    text = " ".join(str(i) for i in range(100))
    chunks = chunk_text(text, chunk_size=10, overlap=0)
    assert len(chunks) == 10
    for c in chunks:
        assert len(c.split()) == 10


def test_overlap_produces_more_chunks_than_no_overlap():
    text = " ".join(str(i) for i in range(20))
    chunks_no_overlap = chunk_text(text, chunk_size=10, overlap=0)
    chunks_with_overlap = chunk_text(text, chunk_size=10, overlap=5)
    assert len(chunks_with_overlap) > len(chunks_no_overlap)


def test_overlapping_chunks_share_words():
    text = " ".join(str(i) for i in range(30))
    chunks = chunk_text(text, chunk_size=10, overlap=3)
    for i in range(len(chunks) - 1):
        tail = set(chunks[i].split()[-3:])
        head = set(chunks[i + 1].split()[:3])
        assert tail & head, "Adjacent chunks should share overlapping words"


def test_excessive_overlap_is_clamped():
    text = " ".join(["word"] * 20)
    chunks = chunk_text(text, chunk_size=10, overlap=999)
    assert all(len(c.split()) <= 10 for c in chunks)


def test_chunk_size_one_produces_single_word_chunks():
    text = "alpha beta gamma"
    chunks = chunk_text(text, chunk_size=1, overlap=0)
    assert chunks == ["alpha", "beta", "gamma"]
