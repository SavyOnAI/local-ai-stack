import json
from pathlib import Path
from src.ingestion.loader import find_documents
from src.ingestion.extractors.pdf_extractor import extract

if __name__ == "__main__":
    pdf_files = [p for p in find_documents("docs") if p.suffix.lower() == ".pdf"]
    report = []

    for pdf in pdf_files:
        print(f"Scanning {pdf.name}...")
        extract(pdf, report=report)

    with open("logs/pdf_degradation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    by_file = {}
    for entry in report:
        by_file.setdefault(entry["file"], {
            "skipped": 0, "recovered": 0, "recovered_layout": 0,
            "recovered_pdfplumber": 0, "borderline": 0,
        })
        by_file[entry["file"]][entry["status"]] += 1

    print("\n" + "=" * 70)
    print("SUMMARY — pages affected per file")
    print("=" * 70)
    for fname, counts in sorted(by_file.items()):
        total_bad = sum(counts.values())
        recovered_total = counts["recovered"] + counts["recovered_layout"] + counts["recovered_pdfplumber"]
        print(f"{fname}: {total_bad} pages flagged "
              f"(skipped={counts['skipped']}, recovered={recovered_total} "
              f"[layout={counts['recovered_layout']}, pdfplumber={counts['recovered_pdfplumber']}], "
              f"borderline={counts['borderline']})")

    total_skipped = sum(c["skipped"] for c in by_file.values())
    print(f"\nTotal pages permanently skipped across corpus: {total_skipped}")
    print("Full detail saved to logs/pdf_degradation_report.json")