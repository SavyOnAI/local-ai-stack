"""
index_documents.py — Ingestion pipeline entry point.

Orchestrates the full pipeline: discover files → extract text →
chunk → embed → store in ChromaDB and BM25 index.

Run from project root:
    python -m src.ingestion.index_documents
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from src.ingestion.loader import load_all_documents
from src.ingestion.chunker import chunk_document
from src.retrieval.vector_store import get_collection, add_chunks
from src.retrieval.bm25_index import build_bm25_index, save_bm25_index
from src.ingestion.embedder import embed_text

load_dotenv()

# config from .env with sensible defaults
DOCS_DIR   = os.getenv("DOCS_DIR",   "docs")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
OVERLAP    = int(os.getenv("OVERLAP",    "150"))


def _make_chunk_id(file_path: str, chunk_index: int) -> str:
    """
    Generate a unique ID for a chunk from its source file and position.

    Args:
        file_path:   Source file path string.
        chunk_index: Position of this chunk within the document.

    Returns:
        A unique string ID — e.g. 'who_guidelines_pdf_chunk_4'
    """
    # use the filename stem only — strip directory and extension
    stem = Path(file_path).stem.lower()

    # replace spaces and special chars with underscores
    safe_stem = "".join(c if c.isalnum() else "_" for c in stem)

    return f"{safe_stem}_chunk_{chunk_index}"


def index_documents(
    docs_dir: str  = DOCS_DIR,
    chunk_size: int = CHUNK_SIZE,
    overlap: int    = OVERLAP,
) -> None:
    """
    Run the full ingestion pipeline for all documents in docs_dir.

    Args:
        docs_dir:   Path to the folder containing source documents.
        chunk_size: Characters per chunk.
        overlap:    Characters shared between adjacent chunks.
    """
    print(f"\n{'='*50}")
    print(f"  Indexing pipeline starting")
    print(f"  Docs dir:   {docs_dir}")
    print(f"  Chunk size: {chunk_size}  |  Overlap: {overlap}")
    print(f"{'='*50}\n")

    # ── step 1: discover and extract all documents ──────────────────
    documents = load_all_documents(docs_dir)

    if not documents:
        print("No documents found. Add files to the docs/ folder and try again.")
        return

    # ── step 2: chunk every document ────────────────────────────────
    all_chunks = []

    for file_path, text in documents.items():
        chunks = chunk_document(file_path, text, chunk_size, overlap)
        all_chunks.extend(chunks)
        print(f"  chunked  {Path(file_path).name}  →  {len(chunks)} chunks")

    print(f"\n  Total chunks across all documents: {len(all_chunks)}")

    # ── step 3: prepare chunks for ChromaDB ─────────────────────────
    chroma_chunks = [
        {
            "id":       _make_chunk_id(c["source"], c["chunk_index"]),
            "text":     c["text"],
            "metadata": {"source": c["source"], "chunk_index": c["chunk_index"]},
        }
        for c in all_chunks
    ]

    # ── step 4: generate embeddings and store in ChromaDB ───────────
    print("\n  Generating embeddings and adding to ChromaDB...")
    collection = get_collection()

    # embed in batches of 50 — avoids overloading Ollama on large corpora
    batch_size = 50
    for i in range(0, len(chroma_chunks), batch_size):
        batch = chroma_chunks[i : i + batch_size]

        # generate embedding for each chunk in this batch
        for chunk in batch:
            chunk["embedding"] = embed_text(chunk["text"], mode="document")

        add_chunks(collection, batch)
        print(f"  embedded and stored chunks {i+1}–{min(i+batch_size, len(chroma_chunks))} of {len(chroma_chunks)}")

    print(f"  ✓ ChromaDB updated — {len(chroma_chunks)} chunks stored")

    # ── step 5: build BM25 keyword index ────────────────────────────
    print("\n  Building BM25 index...")
    bm25_index = build_bm25_index(chroma_chunks)
    save_bm25_index(bm25_index, chroma_chunks)
    print(f"  ✓ BM25 index built and saved — {len(chroma_chunks)} chunks indexed")


if __name__ == "__main__":
    index_documents()