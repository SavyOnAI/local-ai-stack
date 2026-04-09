# src/retrieval/hybrid_retriever.py

from rank_bm25 import BM25Okapi
from loguru import logger

from src.retrieval.bm25_index import query_bm25


def reciprocal_rank_fusion(
    bm25_results: list[dict],
    vector_results: list[dict],
    k: int = 60,  # smoothing constant from original RRF paper
) -> list[dict]:
    """
    Fuse two ranked lists using Reciprocal Rank Fusion.

    Args:
        bm25_results:   ranked chunks from BM25
        vector_results: ranked chunks from ChromaDB
        k:              smoothing constant — prevents rank-1 dominating
    Returns:
        list of chunk dicts with "rrf_score" added, sorted highest first
    """
    scores = {}  # chunk_id → running RRF score

    for rank, chunk in enumerate(bm25_results):
        chunk_id = chunk["id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)

    for rank, chunk in enumerate(vector_results):
        chunk_id = chunk["id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)

    # rebuild full chunk dicts from the combined pool
    all_chunks = {chunk["id"]: chunk for chunk in bm25_results + vector_results}

    fused = [
        {**all_chunks[chunk_id], "rrf_score": rrf_score}
        for chunk_id, rrf_score in scores.items()
    ]
    fused.sort(key=lambda x: x["rrf_score"], reverse=True)

    return fused


def hybrid_retrieve(
    query: str,
    bm25_index: BM25Okapi,
    bm25_chunks: list[dict],
    chroma_collection,
    embed_fn,
    top_k: int = 20,
) -> list[dict]:
    """
    Run BM25 and vector search, fuse results with RRF, return top_k candidates.

    Args:
        query:            the user's question string
        bm25_index:       loaded BM25Okapi index
        bm25_chunks:      chunk dicts the BM25 index was built from
        chroma_collection: active ChromaDB collection
        embed_fn:         function that takes (text, mode) and returns an embedding
        top_k:            number of fused candidates to return
    Returns:
        list of chunk dicts with "rrf_score" added, sorted highest first
    """
    # --- BM25 retrieval
    bm25_results = query_bm25(bm25_index, bm25_chunks, query, top_k=top_k)

    # --- vector retrieval
    query_embedding = embed_fn(query, mode="query")
    vector_results_raw = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    # flatten ChromaDB's nested structure into flat chunk dicts
    vector_results = [
        {
            "id": vector_results_raw["ids"][0][i],
            "text": vector_results_raw["documents"][0][i],
            "metadata": vector_results_raw["metadatas"][0][i],
        }
        for i in range(len(vector_results_raw["ids"][0]))
    ]

    # --- fuse
    fused = reciprocal_rank_fusion(bm25_results, vector_results)

    logger.info(
        f"Hybrid retrieve — BM25: {len(bm25_results)} | "
        f"Vector: {len(vector_results)} | Fused: {len(fused)}"
    )

    return fused[:top_k]


if __name__ == "__main__":
    from src.ingestion.embedder import embed_text
    from src.retrieval.bm25_index import build_bm25_index, save_bm25_index, load_bm25_index
    from src.retrieval.vector_store import get_collection

    # --- fake chunks
    chunks = [
        {"id": "chunk_001", "text": "The RAGAS faithfulness score measures whether the answer is grounded in retrieved context. The threshold is 0.75."},
        {"id": "chunk_002", "text": "FastAPI exposes a /query endpoint that accepts a question and returns a JSON response with citations."},
        {"id": "chunk_003", "text": "RAGAS provides four metrics: faithfulness, answer relevancy, context precision, and context recall."},
        {"id": "chunk_004", "text": "BM25 is a keyword retrieval algorithm that ranks chunks by term frequency and inverse document frequency."},
        {"id": "chunk_005", "text": "ChromaDB persists the vector index to disk automatically. No server setup is required."},
    ]

    # --- build and save BM25
    print("Building BM25 index...")
    bm25_index = build_bm25_index(chunks)
    save_bm25_index(bm25_index, chunks)
    bm25_index, bm25_chunks = load_bm25_index()
    print("✓ BM25 ready")

    # --- load ChromaDB collection
    print("Loading ChromaDB collection...")
    collection = get_collection()

    # add chunks to ChromaDB if collection is empty
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

    # --- run hybrid retrieval
    query = "What is the RAGAS faithfulness threshold?"
    print(f"\nQuery: '{query}'")
    results = hybrid_retrieve(
        query=query,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        chroma_collection=collection,
        embed_fn=embed_text,
        top_k=3,
    )

    print("\nTop 3 fused results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. [{result['id']}] rrf_score={result['rrf_score']:.4f}")
        print(f"     {result['text'][:80]}...")

    # sanity check
    assert results[0]["id"] == "chunk_001", f"Expected chunk_001 at top, got {results[0]['id']}"
    print("\n✓ Sanity check passed — chunk_001 ranked first as expected")