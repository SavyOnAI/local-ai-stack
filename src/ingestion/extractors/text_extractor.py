"""
text_extractor.py — Extractor for .txt and .md files.

Reads plain text files directly. For markdown files, strips
formatting syntax so the model receives clean prose.
"""

import re
from pathlib import Path


def _clean_markdown(text: str) -> str:
    """
    Remove markdown syntax characters from text.

    Args:
        text: Raw markdown string.

    Returns:
        Plain text with formatting symbols removed.
    """
    # remove images before links — same pattern, image has leading !
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # remove hyperlinks — keep the display text, drop the URL
    text = re.sub(r"\[([^\]]+)\]\(.*?\)", r"\1", text)

    # remove headings — one or more # at start of line
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # remove bold and italic markers
    text = re.sub(r"\*{1,3}|_{1,3}", "", text)

    # remove inline code backticks
    text = re.sub(r"`+", "", text)

    # remove blockquote markers
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    # remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

    # remove HTML tags that sometimes appear in .md files
    text = re.sub(r"<[^>]+>", "", text)

    # collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract(file_path: Path) -> str:
    """
    Extract plain text from a .txt or .md file.

    Args:
        file_path: Path to the .txt or .md file.

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If the file extension is not .txt or .md.
    """
    ext = file_path.suffix.lower()

    if ext not in (".txt", ".md"):
        raise ValueError(f"text_extractor only handles .txt and .md, got: {ext}")

    # read with utf-8, fall back to latin-1 for older files
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="latin-1")

    if ext == ".md":
        text = _clean_markdown(text)

    return text.strip()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.extractors.text_extractor <file>")
        sys.exit(1)

    target = Path(sys.argv[1])

    # check the file exists before attempting extraction
    if not target.exists():
        print(f"Error: file not found — {target}")
        sys.exit(1)

    result = extract(target)

    print(f"--- Extracted {len(result):,} characters from {target.name} ---\n")
    print(result[:500])