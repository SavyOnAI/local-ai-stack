# HTTP requests library — how Python talks to APIs
import requests
# Built-in — reads environment variables
import os
# Reads .env file into environment
from dotenv import load_dotenv


# Load .env values — must run before os.getenv()
load_dotenv()

# Model name from .env, with fallback
MODEL_NAME = os.getenv("MODEL_NAME", "gemma4:26b")
# Ollama's local chat endpoint — same on every Mac
OLLAMA_URL = "http://localhost:11434/api/chat"


def ask_ollama(prompt: str) -> str:
    """
    Send a prompt to Ollama, return the model's text response.

    Args:
        prompt: Full prompt string (system + context + question).
    Returns:
        Model response as a string, or an error message.
    """
    # JSON body Ollama expects — model name + message list + no streaming
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}  # role: user | assistant
        ],
        "stream": False  # True = stream tokens live (Phase 6)
    }

    try:
        # POST to Ollama — json= auto-converts dict, timeout prevents hanging
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        # Raises exception on HTTP errors (404, 500 etc.)
        response.raise_for_status()
        # Dig into response JSON: {"message": {"content": "..."}}
        return response.json()["message"]["content"]

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Is it running?"
    except requests.exceptions.Timeout:
        return "Error: Ollama took too long. Try a shorter prompt."
    except Exception as e:
        return f"Error: {e}"


# Only runs when executing this file directly — not when imported
if __name__ == "__main__":
    test_response = ask_ollama("What does Sun Tzu say about the importance of victory in war?")
    print(f"Model says: {test_response}")

