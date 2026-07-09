from src.retrieval.vector_store import get_collection
from src.retrieval.bm25_index import build_bm25_index, save_bm25_index

collection = get_collection()
count = collection.count()
print(f"ChromaDB chunk count: {count}")

if count != 4869:
    print(f"⚠ Expected 4869, got {count} — do NOT rebuild BM25 from this. Full reindex needed instead.")
else:
    all_data = collection.get(include=["metadatas", "documents"])
    chunks = [
        {"id": cid, "text": doc, "source": meta["source"], "chunk_index": meta["chunk_index"]}
        for cid, doc, meta in zip(all_data["ids"], all_data["documents"], all_data["metadatas"])
    ]
    index = build_bm25_index(chunks)
    save_bm25_index(index, chunks)
    print(f"✓ BM25 index rebuilt from existing {len(chunks)} ChromaDB chunks — no re-embedding required")

if __name__ == "__main__":
    pass
