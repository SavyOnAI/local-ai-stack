"""
loader.py — Format router for document ingestion.

Discovers supported files in a directory and routes each file
to the correct extractor based on its extension.
"""

import os
from pathlib import Path

# All file extensions this pipeline supports
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".pdf",
    ".docx", ".pptx", ".xlsx",
    ".csv", ".html",
}


def find_documents(docs_dir: str) -> list[Path]:
    """
    Walk a directory recursively and return all supported files.

    Args:
        docs_dir: Path to the folder containing source documents.

    Returns:
        List of Path objects, one per supported file found.
    """
    docs_path = Path(docs_dir)

    if not docs_path.exists():
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")

    if not docs_path.is_dir():
        raise NotADirectoryError(f"Expected a directory, got: {docs_dir}")

    found = []
    for file_path in docs_path.rglob("*"):       # walk all subfolders
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(file_path)

    return sorted(found)  # consistent order across runs


def load_document(file_path: Path) -> str:
    """
    Route a single file to its extractor and return extracted text.

    Args:
        file_path: Path object pointing to the file to extract.

    Returns:
        Extracted plain text as a single string.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = file_path.suffix.lower()

    # Import extractors here to avoid circular imports
    if ext in (".txt", ".md"):
        from src.ingestion.extractors.text_extractor import extract as text_extract
        return text_extract(file_path)

    elif ext == ".pdf":
        from src.ingestion.extractors.pdf_extractor import extract as pdf_extract
        return pdf_extract(file_path)

    elif ext == ".docx":
        from src.ingestion.extractors.docx_extractor import extract as docx_extract
        return docx_extract(file_path)

    elif ext == ".pptx":
        from src.ingestion.extractors.pptx_extractor import extract as pptx_extract
        return pptx_extract(file_path)

    elif ext == ".xlsx":
        from src.ingestion.extractors.xlsx_extractor import extract as xlsx_extract
        return xlsx_extract(file_path)

    elif ext == ".csv":
        from src.ingestion.extractors.csv_extractor import extract as csv_extract
        return csv_extract(file_path)

    elif ext == ".html":
        from src.ingestion.extractors.html_extractor import extract as html_extract
        return html_extract(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def load_all_documents(docs_dir: str) -> dict[str, str]:
    """
    Discover and extract text from all supported files in a directory.

    Args:
        docs_dir: Path to the folder containing source documents.

    Returns:
        Dict mapping file path string → extracted text string.
        Files that fail to load are skipped with a warning printed.
    """
    files = find_documents(docs_dir)

    if not files:
        print(f"[loader] No supported documents found in: {docs_dir}")
        return {}

    print(f"[loader] Found {len(files)} document(s) in {docs_dir}")

    results = {}
    for file_path in files:
        try:
            text = load_document(file_path)
            if text.strip():  # skip files that extracted to empty string
                results[str(file_path)] = text
                print(f"  ✓  {file_path.name}  ({len(text):,} chars)")
            else:
                print(f"  ⚠  {file_path.name}  — extracted empty text, skipping")
        except Exception as e:
            print(f"  ✗  {file_path.name}  — failed: {e}")

    return results


if __name__ == "__main__":
    import sys

    # Usage: python -m src.ingestion.loader
    # Or pass a custom docs dir as argument: python -m src.ingestion.loader ./my_docs
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "docs"

    documents = load_all_documents(docs_dir)

    print(f"\n--- Smoke test: {len(documents)} document(s) loaded ---")
    for path, text in documents.items():
        preview = text[:200].replace("\n", " ")
        print(f"\n[{Path(path).name}]\n  {preview}...")