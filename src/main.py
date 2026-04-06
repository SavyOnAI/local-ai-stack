from loader import load_documents
from chunker import chunk_documents
from retriever import retrieve
from prompt import build_prompt
from llm import ask_ollama


def initialise() -> list[dict]:
    """
    Load and chunk all documents at startup.

    Returns:
        Full list of chunks ready for retrieval.
    """
    print("Loading documents...")
    docs = load_documents()

    print("Chunking documents...")
    chunks = chunk_documents(docs)

    print(f"Ready — {len(chunks)} chunks loaded.\n")
    return chunks


def answer_question(query: str, chunks: list[dict]) -> str:
    """
    Run the full RAG pipeline for a single question.

    Args:
        query: The user's question.
        chunks: All chunks from initialise().
    Returns:
        The model's answer as a string.
    """
    top_chunks = retrieve(query, chunks)      # find relevant chunks
    prompt = build_prompt(query, top_chunks)  # assemble prompt
    response = ask_ollama(prompt)             # send to Gemma
    return response


def run():
    """
    Run the interactive Q&A loop until the user types quit or exit.
    """
    print("=== Local RAG Pipeline ===")
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    chunks = initialise()  # load once, reuse every query

    while True:
        query = input("You: ").strip()  # strip removes accidental whitespace

        if not query:       # skip empty input
            continue

        if query.lower() in {"quit", "exit"}:  # clean exit
            print("Goodbye!")
            break

        print("\nThinking...\n")
        answer = answer_question(query, chunks)
        print(f"Gemma: {answer}\n")


# Only runs when executing this file directly
if __name__ == "__main__":
    run()