# src/retrieval/reranker.py

from sentence_transformers import CrossEncoder
from loguru import logger


# module-level cache — loaded once, reused on every query
_reranker_model = None


def get_reranker() -> CrossEncoder:
    """
    Load the cross-encoder model once and cache it for reuse.

    Returns:
        CrossEncoder model ready for inference
    """
    global _reranker_model
    if _reranker_model is None:
        logger.info("Loading cross-encoder model...")
        _reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
        logger.info("✓ Cross-encoder loaded")
    return _reranker_model


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,  # final answer set — tighter than retrieval top_k
) -> list[dict]:
    """
    Score each candidate chunk against the query and return the top_k results.

    Args:
        query:      the user's question string
        candidates: chunk dicts from hybrid retrieval (with rrf_score)
        top_k:      number of reranked results to return
    Returns:
        list of chunk dicts with "rerank_score" added, sorted highest first
    """
    if not candidates:
        logger.warning("Reranker received empty candidate list")
        return []

    model = get_reranker()

    # pair query with each candidate for joint scoring
    pairs = [[query, chunk["text"]] for chunk in candidates]

    # score all pairs in one batch
    scores = model.predict(pairs)

    scored = [
        {**chunk, "rerank_score": float(scores[i])}
        for i, chunk in enumerate(candidates)
    ]
    scored.sort(key=lambda x: x["rerank_score"], reverse=True)

    top = scored[:top_k]
    logger.info(
        f"Reranker — in: {len(candidates)} candidates | "
        f"out: {len(top)} | top score: {top[0]['rerank_score']:.4f}"
    )
    return top


if __name__ == "__main__":
    from src.ingestion.embedder import embed_text
    from src.retrieval.bm25_index import build_bm25_index, save_bm25_index, load_bm25_index
    from src.retrieval.vector_store import get_collection
    from src.retrieval.hybrid_retriever import hybrid_retrieve

    # --- fake chunks
    chunks = [
        {"id": "chunk_001", "text": "The RAGAS faithfulness score measures whether the answer is grounded in retrieved context. The threshold is 0.75."},
        {"id": "chunk_002", "text": "FastAPI exposes a /query endpoint that accepts a question and returns a JSON response with citations."},
        {"id": "chunk_003", "text": "RAGAS provides four metrics: faithfulness, answer relevancy, context precision, and context recall."},
        {"id": "chunk_004", "text": "BM25 is a keyword retrieval algorithm that ranks chunks by term frequency and inverse document frequency."},
        {"id": "chunk_005", "text": "ChromaDB persists the vector index to disk automatically. No server setup is required."},
    ]

    # --- BM25
    print("Building BM25 index...")
    bm25_index = build_bm25_index(chunks)
    save_bm25_index(bm25_index, chunks)
    bm25_index, bm25_chunks = load_bm25_index()
    print("✓ BM25 ready")

    # --- ChromaDB
    print("Loading ChromaDB collection...")
    collection = get_collection()
    if collection.count() == 0:
        print("Collection empty — adding chunks...")
        embeddings = [embed_text(chunk["text"], mode="document") for chunk in chunks]
        collection.add(
            ids=[chunk["id"] for chunk in chunks],
            documents=[chunk["text"] for chunk in chunks],
            embeddings=embeddings,
            metadatas=[{"source": "smoke_test"} for _ in chunks],
        )
        print(f"✓ Added {len(chunks)} chunks to ChromaDB")

    # --- hybrid retrieve
    query = "What is the RAGAS faithfulness threshold?"
    print(f"\nQuery: '{query}'")
    candidates = hybrid_retrieve(
        query=query,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        chroma_collection=collection,
        embed_fn=embed_text,
        top_k=5,
    )
    print(f"✓ Hybrid retrieval returned {len(candidates)} candidates")

    # --- rerank
    print("\nReranking...")
    results = rerank(query=query, candidates=candidates, top_k=3)

    print("\nTop 3 reranked results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. [{result['id']}] rerank_score={result['rerank_score']:.4f}")
        print(f"     {result['text'][:80]}...")

    # sanity check
    assert results[0]["id"] == "chunk_001", f"Expected chunk_001 at top, got {results[0]['id']}"
    print("\n✓ Sanity check passed — chunk_001 ranked first as expected")