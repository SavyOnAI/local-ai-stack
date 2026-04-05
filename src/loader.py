import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Docs folder from .env, defaults to "docs"
DOCS_DIR = os.getenv("DOCS_DIR", "docs")
# File types this loader handles
SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_documents(docs_dir: str = DOCS_DIR) -> list[dict]:
    """
    Load all .txt and .md files from a directory.

    Args:
        docs_dir: Path to the folder containing source documents.
    Returns:
        List of dicts with 'filename' and 'text' keys.
    """
    documents = []
    docs_path = Path(docs_dir)  # string → Path object

    # Bail early if folder doesn't exist
    if not docs_path.exists():
        print(f"Warning: docs folder '{docs_dir}' not found.")
        return documents

    for file_path in docs_path.iterdir():
        # Skip unsupported file types
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            # Read file contents — utf-8 handles special characters correctly
            text = file_path.read_text(encoding="utf-8")
            documents.append({
                "filename": file_path.name,
                "text": text
            })
            print(f"Loaded: {file_path.name} ({len(text)} characters)")

        except Exception as e:
            print(f"Warning: could not read {file_path.name} — {e}")

    return documents


# Only runs when executing this file directly
if __name__ == "__main__":
    docs = load_documents()
    print(f"\nTotal documents loaded: {len(docs)}")
    for doc in docs:
        print(f"  - {doc['filename']}: {len(doc['text'])} characters")