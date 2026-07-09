import pypdf
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from src.ingestion.extractors.pdf_extractor import _avg_word_length


def compare_extraction_modes(file_path, page_num):
    reader = pypdf.PdfReader(file_path)
    page = reader.pages[page_num]
    default_text = page.extract_text()
    layout_text = page.extract_text(extraction_mode="layout")
    return default_text, layout_text


if __name__ == "__main__":
    print("=" * 70)
    print("CURRENTLY FRAGMENTED PAGES — does layout mode fix these?")
    print("=" * 70)
    bad_targets = [
        ("docs/OpenAI_a_practical_guide_to_building_agents.pdf", 1),
        ("docs/RAG_Systems_from_PDFs_Experience_Report.pdf", 14),
        ("docs/Cisco_AI_Agents_and_AI_Frameworks_Overview.pdf", 45),
    ]
    for path, page_num in bad_targets:
        default_text, layout_text = compare_extraction_modes(path, page_num)
        print(f"\n{path} — page {page_num + 1}")
        print(f"  DEFAULT avg word len: {_avg_word_length(default_text):.2f}")
        print(f"  LAYOUT  avg word len: {_avg_word_length(layout_text):.2f}")

    print("\n" + "=" * 70)
    print("CURRENTLY CLEAN PAGES — does layout mode break these?")
    print("=" * 70)
    clean_targets = [
        ("docs/Attention_Is_All_You_Need.pdf", 5),
        ("docs/Synergizing_RAG_and_Reasoning_Systematic_Review.pdf", 10),
    ]
    for path, page_num in clean_targets:
        default_text, layout_text = compare_extraction_modes(path, page_num)
        print(f"\n{path} — page {page_num + 1}")
        print(f"  DEFAULT avg word len: {_avg_word_length(default_text):.2f}")
        print(f"  LAYOUT  avg word len: {_avg_word_length(layout_text):.2f}")