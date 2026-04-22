"""
prompt_builder.py — Assembles the LLM prompt from retrieved chunks.

Formats context chunks with their IDs so the model can cite them,
then builds the full prompt: system instructions + context + question.
"""

SYSTEM_PROMPT = """You are a precise document assistant. Answer the user's question using ONLY the context provided below.

Rules:
- Every factual claim MUST cite its source using the chunk ID in square brackets, e.g. [chunk_id_here].
- If the context does not contain the answer, say: "I could not find this in the provided documents."
- Do not use your training knowledge. Only use the context.
- Be concise and direct."""


def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a labelled context block.

    Args:
        chunks: List of chunk dicts, each with 'chunk_id' and 'text' keys.
    Returns:
        A single string with each chunk labelled by its ID.
    """
    lines = []
    for chunk in chunks:
        chunk_id = chunk["id"]
        text = chunk["text"].strip()
        lines.append(f"[{chunk_id}]\n{text}")
    return "\n\n".join(lines)


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Assemble the full prompt sent to the LLM.

    Args:
        query: The user's question.
        chunks: Retrieved chunks from the retrieval pipeline.
    Returns:
        A formatted prompt string: system prompt + context + question.
    """
    context = format_context(chunks)
    return f"{SYSTEM_PROMPT}\n\n---\nCONTEXT:\n{context}\n\n---\nQUESTION: {query}\n\nANSWER:"


if __name__ == "__main__":
    # smoke test — fake chunks to verify formatting
    test_chunks = [
        {"chunk_id": "notes_md__chunk_001", "text": "RAG stands for Retrieval-Augmented Generation."},
        {"chunk_id": "notes_md__chunk_002", "text": "ChromaDB is a local vector database."},
    ]
    prompt = build_prompt("What is RAG?", test_chunks)
    print(prompt)