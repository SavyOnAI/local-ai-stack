from src.retrieval.vector_store import get_collection

collection = get_collection()
data = collection.get(include=[])
print(data["ids"])

if __name__ == "__main__":
    pass
