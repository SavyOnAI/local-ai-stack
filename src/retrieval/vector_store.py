import chromadb  # local vector database
from loguru import logger  # structured logging


def get_collection(persist_dir: str = "chroma_db", collection_name: str = "documents"):
    """
    Connect to ChromaDB and return a persistent collection.
    Creates the collection if it doesn't exist; opens it if it does.

    Args:
        persist_dir: Folder where ChromaDB writes its files.
        collection_name: Name of the collection to create or open.

    Returns:
        A ChromaDB collection object ready for adding and querying.
    """
    client = chromadb.PersistentClient(path=persist_dir)  # writes to disk automatically
    collection = client.get_or_create_collection(name=collection_name)  # open or create
    logger.info(f"Connected to collection '{collection_name}' at '{persist_dir}'")
    return collection


def add_chunks(collection, chunks: list[dict]) -> None:
    """
    Store a list of chunks in ChromaDB with their embeddings and metadata.

    Args:
        collection: The ChromaDB collection to add to.
        chunks: List of dicts, each with keys: 'id' (str), 'text' (str),
                'embedding' (list[float]), 'metadata' (dict with 'source' and 'chunk_index').
    """
    ids = [chunk["id"] for chunk in chunks]  # unique identifier per chunk
    texts = [chunk["text"] for chunk in chunks]  # raw text stored alongside vector
    embeddings = [chunk["embedding"] for chunk in chunks]  # the vectors
    metadatas = [chunk["metadata"] for chunk in chunks]  # already-built source + chunk_index dict

    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    logger.info(f"Added {len(chunks)} chunks to ChromaDB")


def query_collection(collection, query_vector: list[float], n_results: int = 5) -> list[dict]:
    """
    Find the most semantically similar chunks to a query vector.

    Args:
        collection: The ChromaDB collection to search.
        query_vector: The embedding of the user's query.
        n_results: How many chunks to return (default 5).

    Returns:
        List of dicts with keys: 'id', 'text', 'distance' (lower = more similar).
    """
    results = collection.query(
        query_embeddings=[query_vector],  # ChromaDB expects a list of vectors
        n_results=n_results,
    )

    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "distance": results["distances"][0][i],  # lower distance = more similar
        })

    logger.info(f"Query returned {len(chunks)} results")
    return chunks


if __name__ == "__main__":
    from src.ingestion.embedder import embed_text

    collection = get_collection()

    sample_chunks = [
        {"id": "chunk_001", "text": "RAG stands for Retrieval-Augmented Generation.",
         "metadata": {"source": "smoke_test.txt", "chunk_index": 0}},
        {"id": "chunk_002", "text": "ChromaDB stores vectors and enables semantic search.",
         "metadata": {"source": "smoke_test.txt", "chunk_index": 1}},
        {"id": "chunk_003", "text": "The M1 Max has 64 GB of unified memory.",
         "metadata": {"source": "smoke_test.txt", "chunk_index": 2}},
    ]

    for chunk in sample_chunks:
        chunk["embedding"] = embed_text(chunk["text"], mode="document")

    add_chunks(collection, sample_chunks)

    query = "What does RAG stand for?"
    query_vector = embed_text(query, mode="query")
    results = query_collection(collection, query_vector, n_results=3)

    print("\nQuery:", query)
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text']}")

    meta_check = collection.get(ids=[r["id"] for r in results], include=["metadatas"])
    print("\nMetadata check:", meta_check["metadatas"])