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
    clean_files = [
        "docs/Attention_Is_All_You_Need.pdf",
        "docs/Synergizing_RAG_and_Reasoning_Systematic_Review.pdf",
        "docs/AWS_agentic_ai_frameworks.pdf",
        "docs/imda_sg_mgf_for_agentic_ai.pdf",
        "docs/Agentic_AI_Frameworks_Architectures_Protocols_and_Design_Challenges.pdf",
        "docs/Microsoft_Human_Agent_Framework.pdf",
        "docs/The_2025_AI_Agent_Index.pdf",
    ]

    all_short, all_long = [], []

    for path in clean_files:
        reader = pypdf.PdfReader(path)
        total = len(reader.pages)
        sample_idxs = sorted(set([0, total // 4, total // 2, (3 * total) // 4, total - 1]))
        for idx in sample_idxs:
            text = reader.pages[idx].extract_text()
            if not text or not text.strip():
                continue
            short_frac, long_frac = _tail_fraction(text)
            all_short.append(short_frac)
            all_long.append(long_frac)
            print(f"{Path(path).name} p{idx+1}: short={short_frac:.3f} long={long_frac:.3f}")

    print("\n--- Summary across all clean pages sampled ---")
    print(f"short_frac  min={min(all_short):.3f}  max={max(all_short):.3f}  avg={sum(all_short)/len(all_short):.3f}")
    print(f"long_frac   min={min(all_long):.3f}  max={max(all_long):.3f}  avg={sum(all_long)/len(all_long):.3f}")