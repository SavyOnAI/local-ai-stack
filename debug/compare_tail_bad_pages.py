import pypdf
from pathlib import Path


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


if __name__ == "__main__":
    bad_pages = [
        ("docs/Cisco_AI_Agents_and_AI_Frameworks_Overview.pdf", 45, "default"),
        ("docs/Cisco_AI_Agents_and_AI_Frameworks_Overview.pdf", 46, "default"),
        ("docs/OpenAI_a_practical_guide_to_building_agents.pdf", 1, "default"),
        ("docs/Attention_Is_All_You_Need.pdf", 5, "layout"),
    ]

    for path, page_idx, mode in bad_pages:
        reader = pypdf.PdfReader(path)
        kwargs = {"extraction_mode": mode} if mode == "layout" else {}
        text = reader.pages[page_idx].extract_text(**kwargs)
        short_frac, long_frac = _tail_fraction(text)
        print(f"{Path(path).name} p{page_idx+1} [{mode}]: short={short_frac:.3f} long={long_frac:.3f}")