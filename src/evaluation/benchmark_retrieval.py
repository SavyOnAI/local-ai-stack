"""
benchmark_retrieval.py — Compare hybrid retrieval vs BM25-only on the eval set.

Scores context_precision and context_recall only — these measure retrieval
quality directly. Faithfulness/answer_relevancy are generation-quality and
are skipped here to save judge-model runtime (DEC-006 validation, not a
generation benchmark).
"""

import json
import time
from pathlib import Path

from ragas import evaluate
from ragas.run_config import RunConfig
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import context_precision, context_recall

from src.generation.query_pipeline import load_indexes
from src.evaluation.evaluator import (
    load_eval_set,
    build_ragas_llm,
    build_ragas_dataset,
    LocalEmbeddings,
    _mean,
)

RESULTS_PATH = Path("src/evaluation/retrieval_comparison.json")
MODES = ["hybrid", "bm25_only"]


def score_mode(
    mode: str,
    eval_items: list[dict],
    bm25_index,
    bm25_chunks: list[dict],
    collection,
    metrics: list,
    limit: int | None = None,
) -> dict:
    """
    Run the eval set through one retrieval mode and score context_precision
    and context_recall.

    Returns:
        Dict with the two scores plus how many questions were evaluated.
    """
    print(f"\n{'='*50}\nRETRIEVAL MODE: {mode}\n{'='*50}")

    dataset = build_ragas_dataset(
        eval_items=eval_items,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        collection=collection,
        limit=limit,
        retrieval_mode=mode,
        timeout=300,  # bumped after DEC-017-pattern timeout on Q7 generation stage
    )

    run_config = RunConfig(timeout=300, max_retries=2, max_workers=1)
    result = evaluate(
        dataset,
        metrics=metrics,
        embeddings=LocalEmbeddings(),
        run_config=run_config,
    )

    return {
        "context_precision": _mean(result["context_precision"]),
        "context_recall":    _mean(result["context_recall"]),
        "questions_evaluated": len(dataset),
    }


def run_comparison(limit: int | None = None) -> dict:
    """
    Full comparison: hybrid vs bm25_only, same eval set, same judge.

    Args:
        limit: if set, only run the first N questions (smoke test).
    Returns:
        Dict of mode -> scores.
    """
    print("Loading indexes...")
    bm25_index, bm25_chunks, collection = load_indexes()

    eval_items = load_eval_set()

    ragas_llm = build_ragas_llm()
    metrics = [context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm

    results = {}
    start = time.time()
    for mode in MODES:
        results[mode] = score_mode(
            mode, eval_items, bm25_index, bm25_chunks, collection, metrics, limit=limit
        )
    elapsed = time.time() - start

    # ── print comparison ──
    print(f"\n{'='*50}\nHYBRID vs BM25-ONLY — RETRIEVAL COMPARISON\n{'='*50}")
    for mode in MODES:
        r = results[mode]
        print(f"  {mode:<12} context_precision={r['context_precision']:.4f}  "
              f"context_recall={r['context_recall']:.4f}  (n={r['questions_evaluated']})")
    print(f"{'='*50}\nTotal time: {elapsed:.1f}s")

    output = {"results": results, "total_time_s": round(elapsed, 1)}
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {RESULTS_PATH}")

    return results


if __name__ == "__main__":
    import sys
    full_run = "--full" in sys.argv
    limit = None if full_run else 2

    if limit:
        print("SMOKE TEST — 2 questions per mode only.")
        print("Pass --full to run all 30.\n")

    run_comparison(limit=limit)