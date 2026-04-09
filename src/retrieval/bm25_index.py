# src/retrieval/bm25_index.py

import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi  # the BM25 variant used in production systems
from loguru import logger


# where the index file lives on disk
BM25_INDEX_PATH = Path("bm25_index.pkl")


def build_bm25_index(chunks: list[dict]) -> BM25Okapi:
    """
    Build a BM25 index from a list of chunk dicts.

    Args:
        chunks: list of dicts, each with at least a "text" key
    Returns:
        tuple of (BM25Okapi index, list of chunk dicts)
    """
    # pull the raw text out of each chunk dict
    texts = [chunk["text"] for chunk in chunks]

    # tokenise — BM25 works on word lists, not raw strings
    tokenised = [text.lower().split() for text in texts]

    logger.info(f"Building BM25 index over {len(tokenised)} chunks")
    index = BM25Okapi(tokenised)

    return index


def save_bm25_index(index: BM25Okapi, chunks: list[dict], path: Path = BM25_INDEX_PATH) -> None:
    """
    Persist the BM25 index and its source chunks to disk.

    Args:
        index:  the BM25Okapi object to save
        chunks: the chunk dicts the index was built from
        path:   file path to write to (default: bm25_index.pkl)
    """
    payload = {
        "index": index,
        "chunks": chunks,  # stored together so load gives you everything you need
    }
    with open(path, "wb") as f:
        pickle.dump(payload, f)

    logger.info(f"BM25 index saved → {path} ({len(chunks)} chunks)")


def load_bm25_index(path: Path = BM25_INDEX_PATH) -> tuple[BM25Okapi, list[dict]]:
    """
    Load a previously saved BM25 index from disk.

    Args:
        path: file path to load from (default: bm25_index.pkl)
    Returns:
        tuple of (BM25Okapi index, list of chunk dicts)
    Raises:
        FileNotFoundError if the index file doesn't exist yet
    """
    if not path.exists():
        raise FileNotFoundError(
            f"No BM25 index found at {path}. Run build_bm25_index() first."
        )

    with open(path, "rb") as f:
        payload = pickle.load(f)

    logger.info(f"BM25 index loaded ← {path} ({len(payload['chunks'])} chunks)")
    return payload["index"], payload["chunks"]


def query_bm25(
    index: BM25Okapi,
    chunks: list[dict],
    query: str,
    top_k: int = 20,  # deliberately wide — reranker will narrow this down later
) -> list[dict]:
    """
    Score all chunks against the query and return the top_k results.

    Args:
        index:  the BM25Okapi index
        chunks: the chunk dicts the index was built from
        query:  the user's question string
        top_k:  how many results to return
    Returns:
        list of dicts, each chunk dict with a "bm25_score" key added,
        sorted highest score first
    """
    # tokenise the query the same way as the chunks
    tokenised_query = query.lower().split()

    # scores is a numpy array — one score per chunk, same order as chunks
    scores = index.get_scores(tokenised_query)

    # pair each chunk with its score, then sort descending
    scored = [
        {**chunk, "bm25_score": float(scores[i])}
        for i, chunk in enumerate(chunks)
    ]
    scored.sort(key=lambda x: x["bm25_score"], reverse=True)

    top = scored[:top_k]
    logger.debug(f"BM25 top-1 score: {top[0]['bm25_score']:.4f} | query: '{query}'")

    return top

if __name__ == "__main__":
    # --- fake chunks — mirrors real chunk structure
    chunks = [
        {"id": "chunk_001", "text": "The RAGAS faithfulness score measures whether the answer is grounded in retrieved context. The threshold is 0.75."},
        {"id": "chunk_002", "text": "FastAPI exposes a /query endpoint that accepts a question and returns a JSON response with citations."},
        {"id": "chunk_003", "text": "RAGAS provides four metrics: faithfulness, answer relevancy, context precision, and context recall."},
        {"id": "chunk_004", "text": "BM25 is a keyword retrieval algorithm that ranks chunks by term frequency and inverse document frequency."},
        {"id": "chunk_005", "text": "ChromaDB persists the vector index to disk automatically. No server setup is required."},
    ]

    # build
    print("Building index...")
    index = build_bm25_index(chunks)
    print("✓ Index built")

    # save
    print("Saving index...")
    save_bm25_index(index, chunks)
    print("✓ Saved to bm25_index.pkl")

    # load
    print("Loading index...")
    loaded_index, loaded_chunks = load_bm25_index()
    print(f"✓ Loaded — {len(loaded_chunks)} chunks")

    # query
    query = "What is the RAGAS faithfulness threshold?"
    print(f"\nQuery: '{query}'")
    results = query_bm25(loaded_index, loaded_chunks, query, top_k=3)

    print("\nTop 3 results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. [{result['id']}] score={result['bm25_score']:.4f}")
        print(f"     {result['text'][:80]}...")

    # sanity check
    assert results[0]["id"] == "chunk_001", f"Expected chunk_001 at top, got {results[0]['id']}"
    print("\n✓ Sanity check passed — chunk_001 ranked first as expected")