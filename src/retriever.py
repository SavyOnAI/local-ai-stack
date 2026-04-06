import os
from dotenv import load_dotenv

load_dotenv()

# Number of top chunks to return per query
TOP_K = int(os.getenv("TOP_K", "5"))


# common words that add noise to scoring — filter these out
STOP_WORDS = {
    "what", "does", "the", "is", "a", "an", "and", "or", "to",
    "in", "of", "it", "that", "this", "for", "on", "are", "was",
    "say", "says", "about", "how", "why", "who", "do", "did"
}

def score_chunk(chunk_text: str, query: str) -> float:
    """
    Score a chunk by how many meaningful query words appear in it.

    Args:
        chunk_text: The chunk's text content.
        query: The user's question.
    Returns:
        Float score — higher means more relevant.
    """
    chunk_lower = chunk_text.lower()
    query_words = query.lower().split()

    # filter out stop words — only score on meaningful words
    meaningful_words = [w for w in query_words if w not in STOP_WORDS]

    # fall back to all words if everything got filtered out
    words_to_score = meaningful_words if meaningful_words else query_words

    score = sum(1 for word in words_to_score if word in chunk_lower)
    return float(score)


def retrieve(query: str, chunks: list[dict],
            top_k: int = TOP_K) -> list[dict]:
    """
    Return the top_k most relevant chunks for a query.

    Args:
        query: The user's question.
        chunks: Full list of chunks from chunk_documents().
        top_k: Number of chunks to return.
    Returns:
        List of top_k chunk dicts, highest scoring first.
    """
    # pair each chunk with its score
    scored = []
    for chunk in chunks:
        score = score_chunk(chunk["text"], query)
        scored.append((score, chunk))  # (score, chunk) tuple

    # sort highest score first
    scored.sort(key=lambda x: x[0], reverse=True)

    # strip scores — return just the chunk dicts
    return [chunk for score, chunk in scored[:top_k]]


# Only runs when executing this file directly
if __name__ == "__main__":
    from loader import load_documents
    from chunker import chunk_documents

    docs = load_documents()
    chunks = chunk_documents(docs)

    query = "What is the best strategy in war?"
    results = retrieve(query, chunks)

    print(f"\nQuery: {query}")
    print(f"Top {len(results)} chunks:\n")
    for i, chunk in enumerate(results):
        print(f"  [{i+1}] {chunk['chunk_id']}")
        print(f"       {chunk['text'][:150]}...")
        print()