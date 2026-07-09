from src.generation.query_pipeline import load_indexes
from src.retrieval.bm25_index import query_bm25
from src.retrieval.vector_store import query_collection
from src.ingestion.embedder import embed_text

if __name__ == "__main__":
    bm25_index, bm25_chunks, collection = load_indexes()

    checks = [
        ("What two authentication measures does Singapore's Model AI Governance Framework for Agentic AI recommend for agent security?",
         "imda_sg_mgf_for_agentic_ai_chunk_99"),
        ("What four main topics does OpenAI's practical guide to building agents cover, based on its table of contents?",
         "openai_a_practical_guide_to_building_agents_chunk_0"),
    ]

    for query, target_id in checks:
        print("=" * 70)
        print("Q:", query)
        print("Target chunk:", target_id)

        bm25_results = query_bm25(bm25_index, bm25_chunks, query, top_k=20)
        bm25_ids = [r["id"] for r in bm25_results]
        if target_id in bm25_ids:
            print(f"  BM25:   FOUND at rank {bm25_ids.index(target_id) + 1}")
        else:
            print("  BM25:   NOT in top 20")

        query_vector = embed_text(query, mode="query")
        vector_results = query_collection(collection, query_vector, n_results=15)
        vector_ids = [r["id"] for r in vector_results]
        if target_id in vector_ids:
            print(f"  Vector: FOUND at rank {vector_ids.index(target_id) + 1}")
        else:
            print("  Vector: NOT in top 15")