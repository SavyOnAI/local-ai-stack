"""
main.py — Terminal Q&A loop for local-ai-stack (Phase 2 pipeline).

Loads BM25 + ChromaDB indexes once at startup, then runs the full
hybrid retrieval → rerank → generation → citation validation pipeline
for each question via src.generation.query_pipeline.

Was previously wired to the Phase 1 keyword-only pipeline (loader/chunker/
retriever/prompt/llm) — flagged as stale and fixed on Day 13.
"""

from src.generation.query_pipeline import load_indexes, query as run_query


def initialise() -> tuple:
    """
    Load BM25 index and ChromaDB collection once at startup.

    Returns:
        Tuple of (bm25_index, bm25_chunks, collection) — same shape
        query_pipeline.query() expects on every call.
    """
    print("Loading indexes...")
    bm25_index, bm25_chunks, collection = load_indexes()
    print("Ready.\n")
    return bm25_index, bm25_chunks, collection


def answer_question(query: str, indexes: tuple) -> dict:
    """
    Run the full RAG pipeline for a single question.

    Args:
        query:   The user's question.
        indexes: Tuple from initialise() — (bm25_index, bm25_chunks, collection).
    Returns:
        Full pipeline result dict: answer, citations_valid, sources,
        invalid_citations, prompt_tokens, response_tokens, chunks_used.
    """
    bm25_index, bm25_chunks, collection = indexes
    return run_query(
        question=query,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        collection=collection,
    )


def run():
    """
    Run the interactive Q&A loop until the user types quit or exit.
    """
    print("=== local-ai-stack — RAG Pipeline ===")
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    indexes = initialise()  # load once, reuse every query

    while True:
        query = input("You: ").strip()  # strip removes accidental whitespace

        if not query:       # skip empty input
            continue

        if query.lower() in {"quit", "exit"}:  # clean exit
            print("Goodbye!")
            break

        print("\nThinking...\n")
        result = answer_question(query, indexes)

        print(f"Answer: {result['answer']}\n")
        if not result["citations_valid"]:
            print(f"⚠ Citation warning — unverified: {result['invalid_citations']}\n")


# Only runs when executing this file directly
if __name__ == "__main__":
    run()