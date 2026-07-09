from src.retrieval.vector_store import get_collection

collection = get_collection()
all_chunks = collection.get(include=["metadatas", "documents"])

metadatas = all_chunks["metadatas"]
none_count = sum(1 for m in metadatas if m is None)
total = len(metadatas)

print(f"Total chunks: {total}")
print(f"Chunks with no metadata: {none_count}")

if none_count:
    bad_ids = [
        all_chunks["ids"][i]
        for i, m in enumerate(metadatas)
        if m is None
    ]
    print(f"\nFirst 5 affected chunk IDs:")  # noqa: F541
    for cid in bad_ids[:5]:
        idx = all_chunks["ids"].index(cid)
        text_preview = all_chunks["documents"][idx][:150]
        print(f"  {cid} → {text_preview!r}")

if __name__ == "__main__":
    pass