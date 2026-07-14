"""
schemas.py — Pydantic request/response models for the FastAPI server.

Defines the typed shape of every request body and response for
/health, /query, and /index. No logic here — validation only.
"""

from pydantic import BaseModel
from typing import List


class QueryRequest(BaseModel):
    """Defines what a POST /query request body must look like."""
    question: str


class QueryResponse(BaseModel):
    """Defines what POST /query returns."""
    answer: str
    citations_valid: bool
    sources: List[str]
    invalid_citations: List[str]


class IndexRequest(BaseModel):
    """Defines what a POST /index request body must look like."""
    docs_dir: str = "docs"


class IndexResponse(BaseModel):
    """Defines what POST /index returns."""
    status: str
    documents_indexed: int
    chunks_created: int


class HealthResponse(BaseModel):
    """Defines what GET /health returns."""
    status: str
    model: str