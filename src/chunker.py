import os
from dotenv import load_dotenv

load_dotenv()

# Chunk size and overlap from .env — int() converts string to number
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))


def chunk_text(text: str, filename: str,
               chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split a document's text into overlapping chunks.

    Args:
        text: Full document text to split.
        filename: Source filename — stored with each chunk for traceability.
        chunk_size: Maximum characters per chunk.
        overlap: Characters repeated between consecutive chunks.
    Returns:
        List of dicts with 'chunk_id', 'filename', 'text', and 'char_start' keys.
    """
    chunks = []
    start = 0       # cursor position in the document
    chunk_index = 0  # increments with each chunk

    while start < len(text):
        end = start + chunk_size             # end boundary of this chunk
        chunk_text_slice = text[start:end]   # slice characters from text

        chunks.append({
            "chunk_id": f"{filename}_{chunk_index}",  # unique ID for citation tracking
            "filename": filename,
            "text": chunk_text_slice,
            "char_start": start   # position in original doc — useful for debugging
        })

        chunk_index += 1
        start += chunk_size - overlap  # move forward minus overlap to create repeat region

    return chunks


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk all documents from loader output.

    Args:
        documents: List of dicts from load_documents().
    Returns:
        Flat list of all chunks across all documents.
    """
    all_chunks = []
    for doc in documents:
        # Chunk each doc and add results to the master list
        doc_chunks = chunk_text(doc["text"], doc["filename"])
        all_chunks.extend(doc_chunks)
        print(f"Chunked: {doc['filename']} → {len(doc_chunks)} chunks")
    return all_chunks


# Only runs when executing this file directly
if __name__ == "__main__":
    from loader import load_documents

    docs = load_documents()
    chunks = chunk_documents(docs)

    print(f"\nTotal chunks: {len(chunks)}")
    print("\nFirst chunk preview:")
    print(f"  ID: {chunks[0]['chunk_id']}")
    print(f"  Text: {chunks[0]['text'][:200]}...")