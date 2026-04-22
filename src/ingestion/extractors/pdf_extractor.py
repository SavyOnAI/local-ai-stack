"""
pdf_extractor.py — Extractor for .pdf files.

Extracts text page by page using pypdf.
Image-only pages (no text layer) are silently skipped.
"""

from pathlib import Path
import pypdf


def extract(file_path: Path) -> str:
    """
    Extract plain text from a PDF file.

    Args:
        file_path: Path to the .pdf file.

    Returns:
        Extracted text as a single string, with pages separated by
        a blank line. Returns empty string if no text layer found.

    Raises:
        ValueError: If the file extension is not .pdf.
    """
    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"pdf_extractor only handles .pdf, got: {file_path.suffix}")

    pages = []

    with open(file_path, "rb") as f:          # open in binary mode — PDFs are not plain text
        reader = pypdf.PdfReader(f)
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()

            if not text or not text.strip():   # skip image-only pages
                continue

            pages.append(text.strip())

    if not pages:
        print(f"  [pdf_extractor] Warning: no text layer found in {file_path.name}")
        return ""

    return "\n\n".join(pages)                  # blank line between pages


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.extractors.pdf_extractor <file.pdf>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"Error: file not found — {target}")
        sys.exit(1)

    result = extract(target)

    print(f"--- Extracted {len(result):,} characters from {target.name} ---\n")
    print(result[:500])