"""
query_pipeline.py — End-to-end RAG query: retrieve, rerank, generate, validate.

Load indexes once with load_indexes(), then call query() for each question.
Logs one structured JSON line per query to logs/pipeline.jsonl with
per-stage latency and token counts.
"""

import time
import json

from loguru import logger
from src.ingestion.embedder import embed_text
from src.retrieval.bm25_index import load_bm25_index
from src.retrieval.vector_store import get_collection
from src.retrieval.hybrid_retriever import hybrid_retrieve
from src.retrieval.reranker import rerank, get_reranker
from src.generation.prompt_builder import build_prompt
from src.generation.llm import ask_ollama
from src.generation.citation_validator import validate_citations

def _flat_json_sink(message):
    record = message.record
    line = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        **record["extra"],
    }
    with open("logs/pipeline.jsonl", "a") as f:
        f.write(json.dumps(line) + "\n")

logger.add(_flat_json_sink)
# JSON lines, rotate at 10MB so the file never grows unbounded
# commented below to try _flat_json_sink instead, which is simpler and avoids loguru's JSON formatting quirks
# logger.add("logs/pipeline.jsonl", serialize=True, rotation="10 MB")


def load_indexes() -> tuple:
    """
    Load BM25 index, ChromaDB collection, and reranker model.
 
    Returns:
        Tuple of (bm25_index, bm25_chunks, collection).
    """
    bm25_index, bm25_chunks = load_bm25_index()
    collection = get_collection()
    get_reranker()  # warm the cross-encoder now, not on the first query
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
        top_k:       Number of chunks to pass to the LLM.
    Returns:
        Dict with answer, citation validity, sources, and token counts.
    """
    pipeline_start = time.perf_counter()

    # retrieve candidates from both indexes
    stage_start = time.perf_counter()
    candidates = hybrid_retrieve(
        query=question,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        chroma_collection=collection,
        embed_fn=embed_text,
        top_k=top_k * 3,  # fetch wide, reranker trims
    )
    retrieval_ms = (time.perf_counter() - stage_start) * 1000

    # rerank and keep best top_k
    stage_start = time.perf_counter()
    reranked = rerank(question, candidates, top_k=top_k)
    rerank_ms = (time.perf_counter() - stage_start) * 1000

    # build prompt and call the model
    stage_start = time.perf_counter()
    prompt = build_prompt(question, reranked)
    llm_result = ask_ollama(prompt)
    generation_ms = (time.perf_counter() - stage_start) * 1000

    # validate citations in the response
    stage_start = time.perf_counter()
    citation_result = validate_citations(llm_result["response"], reranked)
    validation_ms = (time.perf_counter() - stage_start) * 1000

    total_ms = (time.perf_counter() - pipeline_start) * 1000

    result = {
        "question": question,
        "answer": llm_result["response"],
        "citations_valid": citation_result["is_valid"],
        "invalid_citations": citation_result["invalid_ids"],
        "sources": citation_result["cited_ids"],
        "prompt_tokens": llm_result["prompt_tokens"],
        "response_tokens": llm_result["response_tokens"],
        "chunks_used": [c["id"] for c in reranked],
    }

    # one structured log line per query — this is the row observability reads later
    logger.info(
        "query_complete",
        question=question,
        retrieval_ms=round(retrieval_ms, 1),
        rerank_ms=round(rerank_ms, 1),
        generation_ms=round(generation_ms, 1),
        validation_ms=round(validation_ms, 1),
        total_ms=round(total_ms, 1),
        prompt_tokens=result["prompt_tokens"],
        response_tokens=result["response_tokens"],
        citations_valid=result["citations_valid"],
        chunks_used=result["chunks_used"],
    )

    return result


if __name__ == "__main__":
    print("Loading indexes...")
    bm25_index, bm25_chunks, collection = load_indexes()
    print("Ready.\n")

    test_question = "What safety evaluations were performed on Claude Opus?"

    print(f"Question: {test_question}\n")
    result = query(test_question, bm25_index, bm25_chunks, collection)

    print(f"Answer:\n{result['answer']}\n")
    print(f"Citations valid:  {result['citations_valid']}")
    print(f"Invalid citations: {result['invalid_citations']}")
    print(f"Sources cited:   {result['sources']}")
    print(f"Chunks used:     {result['chunks_used']}")
    print(f"Prompt tokens:   {result['prompt_tokens']}")
    print(f"Response tokens: {result['response_tokens']}")
    print("\nCheck logs/pipeline.jsonl for the structured log line.")