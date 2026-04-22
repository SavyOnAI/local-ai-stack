"""
csv_extractor.py — Extractor for .csv files.

Converts each row into a natural language sentence using the header
row as column labels. This gives the LLM the context it needs to
understand what each value means.
"""

import csv
from pathlib import Path


def _row_to_sentence(headers: list[str], row: list[str]) -> str:
    """
    Convert a single CSV row into a natural language sentence.

    Args:
        headers: List of column header strings.
        row:     List of cell value strings for this row.

    Returns:
        A readable sentence pairing each header with its value.
    """
    pairs = []
    for header, value in zip(headers, row):
        header = header.strip()
        value = value.strip()
        if header and value:                   # skip empty headers or cells
            pairs.append(f"{header} is {value}")

    return ". ".join(pairs) + "." if pairs else ""


def extract(file_path: Path) -> str:
    """
    Extract text from a CSV file by converting rows to sentences.

    Args:
        file_path: Path to the .csv file.

    Returns:
        One sentence per data row, joined by newlines.
        Returns empty string if the file has no data rows.

    Raises:
        ValueError: If the file extension is not .csv.
    """
    if file_path.suffix.lower() != ".csv":
        raise ValueError(f"csv_extractor only handles .csv, got: {file_path.suffix}")

    # try utf-8 first, fall back to cp1252 for Excel-exported CSVs
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            text = file_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode {file_path.name} with any known encoding")

    lines = []
    reader = csv.reader(text.splitlines())

    headers = None
    for row in reader:
        if not any(cell.strip() for cell in row):  # skip fully empty rows
            continue

        if headers is None:
            headers = row                       # first non-empty row is the header
            continue

        sentence = _row_to_sentence(headers, row)
        if sentence:
            lines.append(sentence)

    if not lines:
        print(f"  [csv_extractor] Warning: no data rows found in {file_path.name}")
        return ""

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.extractors.csv_extractor <file.csv>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"Error: file not found — {target}")
        sys.exit(1)

    result = extract(target)

    print(f"--- Extracted {len(result):,} characters from {target.name} ---\n")
    print(result[:500])