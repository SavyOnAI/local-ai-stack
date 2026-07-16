"""
llm.py — Sends a prompt to a local Ollama model and returns the response.

Returns response text plus token counts for observability.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:26b")


def ask_ollama(prompt: str, model: str | None = None, timeout: int = 120) -> dict:
    """
    Send a prompt to a local Ollama model and return the response.

    Args:
        prompt: The fully assembled prompt string from prompt_builder.py.
        model:  Ollama model name to use. Defaults to MODEL_NAME from .env
                if not given — pass this explicitly to override for benchmarking.
        timeout: Seconds to wait for a response. Default 120 is fine for
                 gemma4:26b in production. Larger models — especially on a
                 cold load — need more; benchmark.py passes a higher value.
    Returns:
        Dict with 'response' (str), 'prompt_tokens' (int), 'response_tokens' (int).
    """
    payload = {
        "model": model or MODEL_NAME,  # override for benchmarking, default otherwise
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to Ollama. Is it running? Try: ollama serve")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timed out. The model may still be loading — try again.")

    data = response.json()

    return {
        "response": data["response"].strip(),
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "response_tokens": data.get("eval_count", 0),
    }


if __name__ == "__main__":
    # smoke test — single hardcoded question, no retrieval
    print(f"Model: {MODEL_NAME}")
    print("Sending test prompt...\n")

    result = ask_ollama("In one sentence, what is the capital of France?")

    print(f"Response:         {result['response']}")
    print(f"Prompt tokens:    {result['prompt_tokens']}")
    print(f"Response tokens:  {result['response_tokens']}")

    # smoke test the override path too — catches a typo in the param name early
    print("\nModel: ministral-3:3b (override test)")
    result2 = ask_ollama("In one sentence, what is the capital of France?", model="ministral-3:3b")
    print(f"Response: {result2['response']}")