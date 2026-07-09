"""
pdf_extractor.py — Extractor for .pdf files.

Extracts text page by page using pypdf.
Image-only pages (no text layer) are silently skipped.

Each page is checked for extraction corruption using tail-fraction
analysis: fragmentation (words split apart, e.g. "agen t") spikes the
fraction of very short words; fusion (words wrongly merged) spikes the
fraction of very long words. Severe corruption triggers automatic
retries: first pypdf's layout mode, then pdfplumber (which reconstructs
words from measured glyph positions rather than the PDF's declared font
width table — the root cause identified in some corpus PDFs, July 2026).
If all three fail, the page is skipped rather than ingesting garbled
text. Moderate corruption is logged for manual review but not auto-fixed
— see DECISIONS.md for the known-limitations writeup.
"""

from pathlib import Path
import pypdf

HIGH_CONFIDENCE_SHORT = 0.5
HIGH_CONFIDENCE_LONG  = 0.065
BORDERLINE_SHORT      = 0.30


def _tail_fraction(text: str, min_len: int = 2, max_len: int = 15) -> tuple[float, float]:
    """
    Fraction of words at each length extreme.
    Fragmentation spikes short_frac. Fusion spikes long_frac.
    """
    words = text.split()
    if not words:
        return 0.0, 0.0
    short_frac = sum(1 for w in words if len(w) <= min_len) / len(words)
    long_frac = sum(1 for w in words if len(w) >= max_len) / len(words)
    return short_frac, long_frac


def _extract_page_pdfplumber(file_path: Path, page_num: int) -> str:
    """
    Fallback extraction using pdfplumber — reconstructs words from
    measured glyph positions rather than the PDF's font width table.
    Only called when both pypdf modes fail the corruption check.
    """
    import pdfplumber
    with pdfplumber.open(file_path) as pdf:
        return pdf.pages[page_num].extract_text() or ""


def extract(file_path: Path, report: list | None = None) -> str:
    """
    Extract plain text from a PDF file.

    Args:
        file_path: Path to the .pdf file.
        report:    Optional list to append structured corruption records to.

    Returns:
        Extracted text as a single string, pages separated by a blank line.
        Pages that fail pypdf (both modes) and pdfplumber are skipped.

    Raises:
        ValueError: If the file extension is not .pdf.
    """
    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"pdf_extractor only handles .pdf, got: {file_path.suffix}")

    pages = []

    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()

            if not text or not text.strip():
                continue

            short_frac, long_frac = _tail_fraction(text)

            if short_frac > HIGH_CONFIDENCE_SHORT or long_frac > HIGH_CONFIDENCE_LONG:
                layout_text = page.extract_text(extraction_mode="layout")
                layout_short, layout_long = _tail_fraction(layout_text)

                if layout_short <= HIGH_CONFIDENCE_SHORT and layout_long <= HIGH_CONFIDENCE_LONG:
                    print(f"  [pdf_extractor] Recovered page {i+1} of {file_path.name} "
                          f"using layout mode (default short={short_frac:.2f})")
                    if report is not None:
                        report.append({
                            "file": file_path.name, "page": i + 1, "status": "recovered_layout",
                            "default_short": round(short_frac, 3), "layout_short": round(layout_short, 3),
                        })
                    text = layout_text
                else:
                    plumber_text = _extract_page_pdfplumber(file_path, i)
                    plumber_short, plumber_long = _tail_fraction(plumber_text)

                    if plumber_short <= HIGH_CONFIDENCE_SHORT and plumber_long <= HIGH_CONFIDENCE_LONG:
                        print(f"  [pdf_extractor] Recovered page {i+1} of {file_path.name} "
                              f"using pdfplumber (pypdf both modes failed)")
                        if report is not None:
                            report.append({
                                "file": file_path.name, "page": i + 1, "status": "recovered_pdfplumber",
                                "default_short": round(short_frac, 3), "layout_short": round(layout_short, 3),
                                "plumber_short": round(plumber_short, 3),
                            })
                        text = plumber_text
                    else:
                        print(f"  [pdf_extractor] Skipping page {i+1} of {file_path.name} — "
                              f"corrupted in all three extraction methods")
                        if report is not None:
                            report.append({
                                "file": file_path.name, "page": i + 1, "status": "skipped",
                                "default_short": round(short_frac, 3), "layout_short": round(layout_short, 3),
                                "plumber_short": round(plumber_short, 3),
                            })
                        continue

            elif short_frac > BORDERLINE_SHORT:
                print(f"  [pdf_extractor] Warning: page {i+1} of {file_path.name} "
                      f"may be corrupted (short_frac={short_frac:.2f}) — not auto-fixed, "
                      f"manual check recommended")
                if report is not None:
                    report.append({
                        "file": file_path.name, "page": i + 1, "status": "borderline",
                        "default_short": round(short_frac, 3), "layout_short": None,
                    })

            pages.append(text.strip())

    if not pages:
        print(f"  [pdf_extractor] Warning: no usable text found in {file_path.name}")
        return ""

    return "\n\n".join(pages)


if __name__ == "__main__":
    import sys
    from src.ingestion.loader import find_documents

    if len(sys.argv) >= 2:
        target = Path(sys.argv[1])
        if not target.exists():
            print(f"Error: file not found — {target}")
            sys.exit(1)
        result = extract(target)
        print(f"\n--- Extracted {len(result):,} characters from {target.name} ---\n")
        print(result[:500])
    else:
        print("No file given — scanning all PDFs in docs/ for extraction issues...\n")
        pdf_files = [p for p in find_documents("docs") if p.suffix.lower() == ".pdf"]
        for pdf in pdf_files:
            print(f"Checking {pdf.name}...")
            extract(pdf)