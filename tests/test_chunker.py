# tests/test_chunker.py
from src.ingestion.chunker import chunk_text, chunk_document


def test_chunk_text_empty_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text("   ") == []  # whitespace-only counts as empty


def test_chunk_text_overlap_too_large_raises():
    import pytest
    with pytest.raises(ValueError):
        chunk_text("some text here", chunk_size=10, overlap=10)


def test_chunk_text_exact_overlap_behavior():
    text = "aaaa bbbb cccc dddd eeee ffff gggg hhhh"
    chunks = chunk_text(text, chunk_size=15, overlap=5)
    expected = [
        "aaaa bbbb cccc",
        "cccc dddd eeee",
        "eeee ffff gggg",
        "gggg hhhh",
    ]
    assert chunks == expected


def test_chunk_document_attaches_metadata():
    text = "aaaa bbbb cccc dddd eeee ffff gggg hhhh"
    result = chunk_document("docs/sample.txt", text, chunk_size=15, overlap=5)

    assert len(result) == 4
    for i, chunk in enumerate(result):
        assert chunk["source"] == "docs/sample.txt"
        assert chunk["chunk_index"] == i
        assert "text" in chunk and chunk["text"]  # non-empty string present

def test_chunk_text_overlap_equal_to_chunk_size_raises():
    # stride = chunk_size - overlap = 0 → infinite loop if unguarded
    import pytest
    with pytest.raises(ValueError):
        chunk_text("some text here", chunk_size=10, overlap=10)