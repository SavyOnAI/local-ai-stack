"""
citation_validator.py — Checks that every chunk ID cited in a response actually exists.

After the LLM generates a response, this validates that all cited chunk IDs
are present in the retrieved chunks — catching hallucinated citations.
"""

import re


def extract_cited_ids(response: str) -> list[str]:
    """
    Pull all chunk IDs from square brackets in the response.

    Args:
        response: The raw LLM response text.
    Returns:
        List of chunk ID strings found in the response.
    """
    raw_matches = re.findall(r'\[([^\[\]]+_chunk_\d+(?:,\s*[^\[\]]+_chunk_\d+)*)\]', response)
    ids = []
    for match in raw_matches:
        ids.extend(part.strip() for part in match.split(","))
    return ids

def validate_citations(response: str, chunks: list[dict]) -> dict:
    """
    Check that every cited chunk ID exists in the retrieved chunks.

    Args:
        response: The raw LLM response text.
        chunks: The chunks that were passed into the prompt.
    Returns:
        Dict with cited_ids, valid_ids, invalid_ids, and is_valid flag.
    """
    valid_ids = {chunk["id"] for chunk in chunks}
    cited_ids = extract_cited_ids(response)

    invalid = [cid for cid in cited_ids if cid not in valid_ids]

    return {
        "cited_ids": cited_ids,
        "valid_ids": list(valid_ids),
        "invalid_ids": invalid,
        "is_valid": len(invalid) == 0,
    }


if __name__ == "__main__":
    test_chunks = [
        {"chunk_id": "notes_md__chunk_001", "text": "RAG stands for Retrieval-Augmented Generation."},
        {"chunk_id": "notes_md__chunk_002", "text": "ChromaDB is a local vector database."},
    ]

    # good response — cites real IDs
    good_response = "RAG is a technique [notes_md__chunk_001] that uses ChromaDB [notes_md__chunk_002]."
    result = validate_citations(good_response, test_chunks)
    print("GOOD RESPONSE:")
    print(f"  cited:   {result['cited_ids']}")
    print(f"  invalid: {result['invalid_ids']}")
    print(f"  valid:   {result['is_valid']}")

    print()

    # bad response — cites a hallucinated ID
    bad_response = "RAG is a technique [notes_md__chunk_001] that uses [notes_md__chunk_099]."
    result = validate_citations(bad_response, test_chunks)
    print("BAD RESPONSE:")
    print(f"  cited:   {result['cited_ids']}")
    print(f"  invalid: {result['invalid_ids']}")
    print(f"  valid:   {result['is_valid']}")