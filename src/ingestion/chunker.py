"""
chunker.py — Overlap chunker for Phase 2.

Splits extracted document text into overlapping chunks so that
sentences at chunk boundaries are not lost. Each chunk is returned
with metadata identifying its source file and position.
"""

from pathlib import Path

# defaults match Phase 2 PRD spec — override via .env if needed
CHUNK_SIZE = 800
OVERLAP    = 150


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text:       The full document text to chunk.
        chunk_size: Maximum characters per chunk.
        overlap:    Characters shared between adjacent chunks.

    Returns:
        List of text chunk strings.
    """
    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")

    stride = chunk_size - overlap              # how far to advance each step
    chunks = []
    start  = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            # last chunk — take whatever remains
            chunk = text[start:].strip()
        else:
            # find nearest whitespace before hard boundary to avoid mid-word cuts
            boundary = text.rfind(" ", start, end)
            if boundary == -1:
                boundary = end                 # no whitespace found — cut hard
            chunk = text[start:boundary].strip()

        if chunk:
            chunks.append(chunk)

        start += stride

    return chunks


def chunk_document(
    file_path: str,
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[dict]:
    """
    Chunk a document and attach source metadata to each chunk.

    Args:
        file_path:  Path to the source file (used as metadata).
        text:       Extracted text from the document.
        chunk_size: Maximum characters per chunk.
        overlap:    Characters shared between adjacent chunks.

    Returns:
        List of dicts, each with keys:
            text       — the chunk string
            source     — the source file path
            chunk_index — position of this chunk within the document
    """
    chunks = chunk_text(text, chunk_size, overlap)

    return [
        {
            "text":        chunk,
            "source":      file_path,
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.chunker <file.txt>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"Error: file not found — {target}")
        sys.exit(1)

    # read the file directly for smoke test
    raw_text = target.read_text(encoding="utf-8")
    chunks   = chunk_document(str(target), raw_text)

    print(f"--- {len(chunks)} chunks from {target.name} ---\n")
    for c in chunks[:3]:                       # show first 3 chunks only
        print(f"[Chunk {c['chunk_index']}] ({len(c['text'])} chars)")
        print(c["text"][:200])
        print()