import requests  # HTTP calls to Ollama
from loguru import logger  # structured logging

OLLAMA_URL = "http://localhost:11434/api/embeddings"  # embeddings endpoint, not /api/generate
EMBEDDING_MODEL = "nomic-embed-text"  # matches the ollama pull name exactly

def embed_text(text: str, mode: str = "document") -> list[float]:
    """
    Convert a text string into an embedding vector using nomic-embed-text.

    Args:
        text: The text to embed — a chunk, a query, anything.
        mode: "document" for chunks being stored, "query" for user questions.

    Returns:
        A list of floats representing the text's meaning as a vector.
    """
    prefix = "search_query: " if mode == "query" else "search_document: "  # nomic-embed-text requires these prefixes
    prefixed_text = prefix + text  # prepend before sending to Ollama

    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": prefixed_text,  # send the prefixed version
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()

    vector = response.json()["embedding"]
    logger.debug(f"Embedded {len(text)} chars ({mode}) → vector of {len(vector)} dimensions")

    return vector


if __name__ == "__main__":
    test_text = "The RAG pipeline retrieves relevant chunks before generating an answer."
    vector = embed_text(test_text)
    print(f"Vector length: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")