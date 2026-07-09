import pdfplumber
import fitz  # PyMuPDF
from src.ingestion.extractors.pdf_extractor import _tail_fraction

PATH = "docs/OpenAI_a_practical_guide_to_building_agents.pdf"

# known pypdf results from the corpus scan, for direct comparison
known_pypdf = {
    1:  (0.814, 0.462),
    8:  (0.595, 0.045),
    13: (0.608, 0.059),
    17: (0.600, 0.038),
    19: (0.965, 0.364),
    21: (0.531, 0.526),
}


def extract_pdfplumber(path, page_idx):
    with pdfplumber.open(path) as pdf:
        return pdf.pages[page_idx].extract_text() or ""


def extract_pymupdf(path, page_idx):
    doc = fitz.open(path)
    return doc[page_idx].get_text()


if __name__ == "__main__":
    print(f"{'page':<6}{'pypdf_default':<16}{'pypdf_layout':<15}{'pdfplumber':<15}{'pymupdf':<15}")
    for page_idx, (default_short, layout_short) in known_pypdf.items():
        pl_text = extract_pdfplumber(PATH, page_idx)
        pl_short, pl_long = _tail_fraction(pl_text)

        pm_text = extract_pymupdf(PATH, page_idx)
        pm_short, pm_long = _tail_fraction(pm_text)

        print(f"p{page_idx+1:<5}"
              f"{default_short:<16.3f}"
              f"{layout_short:<15.3f}"
              f"{pl_short:.3f}/{pl_long:<9.3f}"
              f"{pm_short:.3f}/{pm_long:.3f}")

        if page_idx == 8:  # page 9 — print full text for a manual eyeball check
            print("\n--- page 9 pdfplumber text (first 300 chars) ---")
            print(pl_text[:300])
            print("\n--- page 9 pymupdf text (first 300 chars) ---")
            print(pm_text[:300])
            print()