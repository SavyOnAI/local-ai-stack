"""
ui/app.py — Gradio chat interface for local-ai-stack.

Talks to the FastAPI server over HTTP (not a direct pipeline import) so the
UI and API stay decoupled — same contract any other client would use.

Run: 1) uvicorn src.api.server:app --reload   (separate terminal)
     2) python ui/app.py
"""

import requests
import gradio as gr
import re

API_URL = "http://127.0.0.1:8000"


def call_api(question: str) -> dict:
    """Sends a question to the FastAPI /query endpoint, returns the parsed JSON response."""
    response = requests.post(f"{API_URL}/query", json={"question": question})
    response.raise_for_status()
    return response.json()


def format_sources(chunk_ids: list[str]) -> list[str]:
    """Strips '_chunk_N' from each ID and returns unique source filenames, in first-seen order."""
    seen = []
    for cid in chunk_ids:
        filename = re.sub(r"_chunk_\d+$", "", cid)
        if filename not in seen:
            seen.append(filename)
    return seen


def format_response(result: dict) -> str:
    """Formats answer + sources + citation warning into one markdown string for display."""
    answer = result.get("answer", "")
    sources = format_sources(result.get("sources", []))
    valid = result.get("citations_valid", True)

    source_lines = "\n".join(f"- {s}" for s in sources) if sources else "No sources returned."
    warning = "" if valid else "\n\n⚠️ Citation validation failed for this response."

    return f"{answer}\n\n**Sources:**\n{source_lines}{warning}"


def chat_fn(message, history):
    """Gradio callback — sends the message to the API, returns formatted response or an error."""
    try:
        result = call_api(message)
    except requests.exceptions.ConnectionError:
        return "Can't reach the API server. Is `uvicorn src.api.server:app` running?"
    except requests.exceptions.HTTPError as e:
        return f"Server error: {e}"

    return format_response(result)


demo = gr.ChatInterface(
    fn=chat_fn,
    title="local-ai-stack — Ask My Docs",
    description="Ask a question grounded in the indexed document corpus.",
)


if __name__ == "__main__":
    demo.launch()