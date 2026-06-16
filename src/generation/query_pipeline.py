"""
query_pipeline.py — End-to-end RAG query: retrieve, rerank, generate, validate.

Load indexes once with load_indexes(), then call query() for each question.
"""

from src.ingestion.embedder import embed_text
from src.retrieval.bm25_index import load_bm25_index
from src.retrieval.vector_store import get_collection
from src.retrieval.hybrid_retriever import hybrid_retrieve
from src.retrieval.reranker import rerank
from src.generation.prompt_builder import build_prompt
from src.generation.llm import ask_ollama
from src.generation.citation_validator import validate_citations


def load_indexes() -> tuple:
    """
    Load BM25 index, ChromaDB collection, and reranker model.

    Returns:
        Tuple of (bm25_index, bm25_chunks, collection).
    """
    bm25_index, bm25_chunks = load_bm25_index()
    collection = get_collection()
    return bm25_index, bm25_chunks, collection


def query(
    question: str,
    bm25_index,
    bm25_chunks: list[dict],
    collection,
    top_k: int = 5,
) -> dict:
    """
    Run a single question through the full RAG pipeline.

    Args:
        question:    The user's question.
        bm25_index:  Loaded BM25 index.
        bm25_chunks: Chunks associated with the BM25 index.
        collection:  ChromaDB collection.
        reranker:    Loaded cross-encoder model.
        top_k:       Number of chunks to pass to the LLM.
    Returns:
        Dict with answer, citation validity, sources, and token counts.
    """
    

    # retrieve candidates from both indexes
    candidates = hybrid_retrieve(
        query=question,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        chroma_collection=collection,
        embed_fn=embed_text,
        top_k=top_k * 3,  # fetch wide, reranker trims
    )

    # rerank and keep best top_k
    reranked = rerank(question, candidates, top_k=top_k)

    # build prompt and call the model
    prompt = build_prompt(question, reranked)
    llm_result = ask_ollama(prompt)

    # validate citations in the response
    citation_result = validate_citations(llm_result["response"], reranked)

    return {
        "question": question,
        "answer": llm_result["response"],
        "citations_valid": citation_result["is_valid"],
        "invalid_citations": citation_result["invalid_ids"],
        "sources": citation_result["cited_ids"],
        "prompt_tokens": llm_result["prompt_tokens"],
        "response_tokens": llm_result["response_tokens"],
        "chunks_used": [c["id"] for c in reranked],
    }


if __name__ == "__main__":
    print("Loading indexes...")
    bm25_index, bm25_chunks, collection = load_indexes()
    print("Ready.\n")

    test_question = "What is the primary model used in this project and why was it chosen?"

    print(f"Question: {test_question}\n")
    result = query(test_question, bm25_index, bm25_chunks, collection)

    print(f"Answer:\n{result['answer']}\n")
    print(f"Citations valid:  {result['citations_valid']}")
    print(f"Invalid citations: {result['invalid_citations']}")
    print(f"Sources cited:   {result['sources']}")
    print(f"Chunks used:     {result['chunks_used']}")
    print(f"Prompt tokens:   {result['prompt_tokens']}")
    print(f"Response tokens: {result['response_tokens']}")