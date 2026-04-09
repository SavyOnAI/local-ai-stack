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
    Store a list of chunks in ChromaDB with their embeddings.

    Args:
        collection: The ChromaDB collection to add to.
        chunks: List of dicts, each with keys: 'id' (str), 'text' (str), 'embedding' (list[float]).
    """
    ids = [chunk["id"] for chunk in chunks]  # unique identifier per chunk
    texts = [chunk["text"] for chunk in chunks]  # raw text stored alongside vector
    embeddings = [chunk["embedding"] for chunk in chunks]  # the vectors

    collection.add(ids=ids, documents=texts, embeddings=embeddings)
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

    # reformat ChromaDB's nested response into a clean flat list
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
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ingestion"))  # add ingestion folder to path
    from embedder import embed_text  # now Python can find it

    # set up collection
    collection = get_collection()

    # create two fake chunks and embed them
    sample_chunks = [
        {"id": "chunk_001", "text": "RAG stands for Retrieval-Augmented Generation."},
        {"id": "chunk_002", "text": "ChromaDB stores vectors and enables semantic search."},
        {"id": "chunk_003", "text": "The M1 Max has 64 GB of unified memory."},
    ]

    for chunk in sample_chunks:
        chunk["embedding"] = embed_text(chunk["text"], mode="document")  # chunks are documents


    add_chunks(collection, sample_chunks)

    # query with something semantically similar to chunk_001
    query = "What does RAG stand for?"
    query_vector = embed_text(query, mode="query")  # queries use query prefix
    results = query_collection(collection, query_vector, n_results=3)

    print("\nQuery:", query)
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text']}")