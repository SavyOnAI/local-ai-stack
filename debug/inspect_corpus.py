from collections import defaultdict
from src.retrieval.vector_store import get_collection
from src.generation.query_pipeline import query, load_indexes

# --- Part 1: manual retrieval smoke test ---
print("=" * 60)
print("RETRIEVAL SMOKE TEST")
print("=" * 60)

bm25_index, bm25_chunks, collection = load_indexes()

test_queries = [
    "What does RAG stand for?",
    "What is the Model Context Protocol?",
    "What is an AI agent?",
]
for q in test_queries:
    result = query(question=q, bm25_index=bm25_index, bm25_chunks=bm25_chunks, collection=collection)
    print(f"\nQ: {q}")
    print(f"A: {result['answer'][:300]}")
    print(f"Chunks used: {result['chunks_used']}")

# --- Part 2: sample real chunk content per source file ---
print("\n" + "=" * 60)
print("CHUNK CONTENT SAMPLE BY SOURCE FILE")
print("=" * 60)

all_chunks = collection.get(include=["metadatas", "documents"])
by_source = defaultdict(list)
for doc, meta in zip(all_chunks["documents"], all_chunks["metadatas"]):
    by_source[meta["source"]].append(doc)

for source, texts in sorted(by_source.items()):
    n = len(texts)
    sample_idxs = sorted(set([0, n // 2, n - 1]))
    print(f"\n=== {source} ({n} chunks) ===")
    for i in sample_idxs:
        preview = texts[i][:250].replace("\n", " ")
        print(f"  [chunk {i}] {preview}")

if __name__ == "__main__":
    pass