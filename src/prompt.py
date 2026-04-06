from dotenv import load_dotenv

load_dotenv()

# Controls how Gemma behaves — stay in context, admit gaps, be concise
SYSTEM_PROMPT = """You are a helpful assistant that answers questions using only the context provided below.
If the answer is not found in the context, say "I don't have enough information to answer that."
Always be concise and factual. Reference the source filename when possible."""


def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a readable context block.

    Args:
        chunks: List of chunk dicts from retrieve().
    Returns:
        Single formatted string with all chunks labelled by source.
    """
    context_parts = []

    for i, chunk in enumerate(chunks):
        # label each chunk with index and source filename
        context_parts.append(
            f"[{i+1}] Source: {chunk['filename']}\n{chunk['text']}"
        )

    # separator makes chunk boundaries visible to the model
    return "\n\n---\n\n".join(context_parts)


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Assemble the full prompt: system instruction + context + question.

    Args:
        query: The user's question.
        chunks: Retrieved chunks from retrieve().
    Returns:
        Complete prompt string ready to send to the LLM.
    """
    context = format_context(chunks)  # chunks → labelled context block

    # three sections in order — system, context, question
    prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""

    return prompt


# Only runs when executing this file directly
if __name__ == "__main__":
    from loader import load_documents
    from chunker import chunk_documents
    from retriever import retrieve

    docs = load_documents()
    chunks = chunk_documents(docs)

    query = "What is the best strategy in war?"
    top_chunks = retrieve(query, chunks)
    prompt = build_prompt(query, top_chunks)

    print(f"Prompt length: {len(prompt)} characters")
    print("\n--- PROMPT PREVIEW ---\n")
    print(prompt[:800])
    print("\n[... truncated ...]")