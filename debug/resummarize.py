import json
with open("logs/pdf_degradation_report.json") as f:
    report = json.load(f)

by_file = {}
for entry in report:
    by_file.setdefault(entry["file"], {
        "skipped": 0, "recovered": 0, "recovered_layout": 0,
        "recovered_pdfplumber": 0, "borderline": 0,
    })
    by_file[entry["file"]][entry["status"]] += 1

for fname, counts in sorted(by_file.items()):
    total_bad = sum(counts.values())
    recovered_total = counts["recovered"] + counts["recovered_layout"] + counts["recovered_pdfplumber"]
    print(f"{fname}: {total_bad} flagged "
          f"(skipped={counts['skipped']}, recovered={recovered_total}, borderline={counts['borderline']})")

total_skipped = sum(c["skipped"] for c in by_file.values())
print(f"\nTotal pages permanently skipped across corpus: {total_skipped}")