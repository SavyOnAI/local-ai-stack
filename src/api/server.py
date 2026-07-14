"""
server.py — FastAPI layer for local-ai-stack.

Exposes /health, /query, /index. Indexes are loaded once at startup, not
per-request. A logging middleware wraps every request with total latency,
status code, and path — separate from the per-stage timing already logged
inside query_pipeline.query().
"""

import os
import time

from fastapi import FastAPI, HTTPException
from loguru import logger

from src.api.schemas import (
    QueryRequest, QueryResponse,
    IndexRequest, IndexResponse, HealthResponse
)
from src.generation.query_pipeline import query as run_query, load_indexes
from src.ingestion.index_documents import index_documents

app = FastAPI(title="local-ai-stack RAG API")

# load indexes once at startup, not per-request — this also warms the
# reranker (see query_pipeline.load_indexes), so the first real request
# doesn't pay the cross-encoder load cost
bm25_index, bm25_chunks, collection = load_indexes()


@app.middleware("http")
async def log_requests(request, call_next):
    """
    Logs one line per HTTP request: method, path, status code, total latency.
    Runs for every endpoint automatically — no per-route logging needed.
    """
    start = time.perf_counter()
    response = await call_next(request)
    total_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        total_ms=round(total_ms, 1),
    )
    return response


@app.get("/health")
def health_check():
    """Confirms the server is running and reports the configured model."""
    model_name = os.getenv("MODEL_NAME", "gemma4:26b")
    return HealthResponse(status="ok", model=model_name)


@app.post("/query")
def query(request: QueryRequest):
    """Runs a question through the full RAG pipeline and returns the answer + citation status."""
    try:
        result = run_query(
            request.question,
            bm25_index,
            bm25_chunks,
            collection,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        answer=result["answer"],
        citations_valid=result["citations_valid"],
        sources=result["sources"],
        invalid_citations=result["invalid_citations"],
    )


@app.post("/index")
def index(request: IndexRequest):
    """Re-indexes all documents in the specified folder."""
    try:
        stats = index_documents(docs_dir=request.docs_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return IndexResponse(
        status="success",
        documents_indexed=stats["documents_indexed"],
        chunks_created=stats["chunks_created"]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)