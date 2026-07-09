from src.generation.query_pipeline import load_indexes
from src.retrieval.bm25_index import query_bm25
from src.retrieval.vector_store import query_collection
from src.ingestion.embedder import embed_text

if __name__ == "__main__":
    bm25_index, bm25_chunks, collection = load_indexes()

    query = "What topics does OpenAI's practical guide to building agents cover?"
    target_id = "openai_a_practical_guide_to_building_agents_chunk_0"

    bm25_results = query_bm25(bm25_index, bm25_chunks, query, top_k=20)
    bm25_ids = [r["id"] for r in bm25_results]
    if target_id in bm25_ids:
        print(f"BM25: FOUND at rank {bm25_ids.index(target_id) + 1}")
    else:
        print("BM25: NOT in top 20")

    query_vector = embed_text(query, mode="query")
    vector_results = query_collection(collection, query_vector, n_results=15)
    vector_ids = [r["id"] for r in vector_results]
    if target_id in vector_ids:
        print(f"Vector: FOUND at rank {vector_ids.index(target_id) + 1}")
    else:
        print("Vector: NOT in top 15")

    # confirm the chunk itself exists and has real content
    check = collection.get(ids=[target_id], include=["documents"])
    print("\nChunk content:", check["documents"])