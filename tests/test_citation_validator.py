# tests/test_citation_validator.py
from src.generation.citation_validator import extract_cited_ids, validate_citations


def test_extract_single_id():
    response = "RAG combines retrieval and generation [notes_md__chunk_001]."
    assert extract_cited_ids(response) == ["notes_md__chunk_001"]


def test_extract_multi_id_bracket():
    # DEC-016 regression test — comma-separated IDs in one bracket
    response = "Both sources agree [file_a_chunk_1, file_b_chunk_2] on this point."
    assert extract_cited_ids(response) == ["file_a_chunk_1", "file_b_chunk_2"]


def test_extract_no_citation():
    response = "I don't know based on the provided context."
    assert extract_cited_ids(response) == []


def test_validate_citations_all_valid():
    chunks = [
        {"id": "notes_md__chunk_001", "text": "..."},
        {"id": "notes_md__chunk_002", "text": "..."},
    ]
    response = "Fact one [notes_md__chunk_001] and fact two [notes_md__chunk_002]."
    result = validate_citations(response, chunks)

    assert result["is_valid"] is True
    assert result["invalid_ids"] == []
    assert set(result["cited_ids"]) == {"notes_md__chunk_001", "notes_md__chunk_002"}


def test_validate_citations_catches_hallucinated_id():
    chunks = [{"id": "notes_md__chunk_001", "text": "..."}]
    response = "Real fact [notes_md__chunk_001], made-up fact [notes_md__chunk_099]."
    result = validate_citations(response, chunks)

    assert result["is_valid"] is False
    assert result["invalid_ids"] == ["notes_md__chunk_099"]