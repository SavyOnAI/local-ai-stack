"""
html_extractor.py — Extractor for .html files.

Strips HTML tags using BeautifulSoup, removes script and style blocks,
and returns clean readable text.
"""

from pathlib import Path
from bs4 import BeautifulSoup


def extract(file_path: Path) -> str:
    """
    Extract plain text from an HTML file.

    Args:
        file_path: Path to the .html file.

    Returns:
        Extracted text with HTML tags removed.

    Raises:
        ValueError: If the file extension is not .html.
    """
    if file_path.suffix.lower() != ".html":
        raise ValueError(f"html_extractor only handles .html, got: {file_path.suffix}")

    try:
        raw_html = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_html = file_path.read_text(encoding="latin-1")

    soup = BeautifulSoup(raw_html, "html.parser")

    # remove script and style blocks — pure noise for a RAG system
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()                        # removes the tag and its contents entirely

    # extract text — separator puts newline between each element's text
    text = soup.get_text(separator="\n")

    # clean up excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)  # drop empty lines

    return cleaned


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.extractors.html_extractor <file.html>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"Error: file not found — {target}")
        sys.exit(1)

    result = extract(target)

    print(f"--- Extracted {len(result):,} characters from {target.name} ---\n")
    print(result[:500])