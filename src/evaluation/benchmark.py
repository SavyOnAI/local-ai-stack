"""
benchmark.py — Compare Ministral 3B, Gemma 4 26B, and Llama 3.3 70B on the
eval set: RAGAS quality scores (faithfulness, relevancy, precision, recall)
plus real speed numbers (tokens/sec, generation latency) on this hardware.

Judge model is fixed to gemma4:26b for every run, regardless of which model
generated the answer — otherwise faithfulness scores aren't comparable
across models.
"""

import json
import time
from pathlib import Path

from ragas import evaluate
from ragas.run_config import RunConfig
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from src.evaluation.evaluator import (
    build_ragas_llm,
    LocalEmbeddings,
    load_eval_set,
    build_ragas_dataset,
    _mean,  # reuse the nan-safe averaging helper — see DEC-017
)
from src.generation.query_pipeline import load_indexes, query as run_query

RESULTS_PATH = Path("src/evaluation/benchmark_results.json")

MODELS = [
    {"label": "Ministral 3B",  "tag": "ministral-3:3b"},
    {"label": "Gemma 4 26B",   "tag": "gemma4:26b"},
    {"label": "Llama 3.3 70B", "tag": "llama3.3"},
]


def warm_up(model_tag: str, bm25_index, bm25_chunks, collection) -> None:
    """
    Run one throwaway query to force Ollama to load this model's weights
    before timing starts. Without this, the first real question absorbs
    the model load cost and inflates that question's generation_ms —
    same issue as the reranker cold-start (DEC-026).
    """
    print(f"  Warming up {model_tag}...")
    run_query(
        question="What is this document about?",
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        collection=collection,
        model=model_tag,
        timeout=600,  # cold model load (up to ~43GB for llama3.3) can exceed 120s alone

    )


def time_model_on_eval_set(
    model_tag: str,
    eval_items: list[dict],
    bm25_index,
    bm25_chunks: list[dict],
    collection,
) -> dict:
    """
    Run every eval question through this model and record per-question
    generation latency and tokens/sec — independent of RAGAS scoring.

    Returns:
        Dict with avg_generation_ms, avg_tokens_per_sec, total_time_s.
    """
    generation_times_ms = []
    tokens_per_sec = []

    for i, item in enumerate(eval_items, 1):
        print(f"  [{i}/{len(eval_items)}] timing...")
        start = time.perf_counter()
        result = run_query(
            question=item["question"],
            bm25_index=bm25_index,
            bm25_chunks=bm25_chunks,
            collection=collection,
            model=model_tag,
            timeout=300,  # warm model, but 70B generation is still slower than the 120s default
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        generation_times_ms.append(elapsed_ms)

        if result["response_tokens"] and elapsed_ms > 0:
            tokens_per_sec.append(result["response_tokens"] / (elapsed_ms / 1000))

    return {
        "avg_generation_ms": round(sum(generation_times_ms) / len(generation_times_ms), 1),
        "avg_tokens_per_sec": round(sum(tokens_per_sec) / len(tokens_per_sec), 1) if tokens_per_sec else 0.0,
        "total_time_s": round(sum(generation_times_ms) / 1000, 1),
    }


def score_model_with_ragas(
    model_tag: str,
    eval_items: list[dict],
    bm25_index,
    bm25_chunks: list[dict],
    collection,
) -> dict:
    """
    Build a RAGAS dataset using this model for generation, judge fixed to
    gemma4:26b, and return the four quality scores.
    """
    ragas_llm = build_ragas_llm()  # always gemma4:26b — the judge, not the model under test
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm

    dataset = build_ragas_dataset(
        eval_items=eval_items,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        collection=collection,
        model=model_tag,
        timeout=300,
    )

    run_config = RunConfig(timeout=300, max_retries=2, max_workers=1)
    result = evaluate(
        dataset,
        metrics=metrics,
        embeddings=LocalEmbeddings(),
        run_config=run_config,
    )

    return {
        "faithfulness":      _mean(result["faithfulness"]),
        "answer_relevancy":  _mean(result["answer_relevancy"]),
        "context_precision": _mean(result["context_precision"]),
        "context_recall":    _mean(result["context_recall"]),
    }


def run_benchmark(limit: int | None = None) -> dict:
    """
    Full benchmark: for each model in MODELS, warm up, time on the eval set,
    then score with RAGAS. Saves combined results to benchmark_results.json.

    Args:
        limit: If set, only use the first N eval questions (smoke test).
    """
    print("Loading indexes...")
    bm25_index, bm25_chunks, collection = load_indexes()

    eval_items = load_eval_set()
    if limit:
        eval_items = eval_items[:limit]
    print(f"Benchmarking on {len(eval_items)} questions.\n")

    all_results = {}

    for model_cfg in MODELS:
        label, tag = model_cfg["label"], model_cfg["tag"]
        print(f"\n{'=' * 50}\n{label}  ({tag})\n{'=' * 50}")

        try:
            warm_up(tag, bm25_index, bm25_chunks, collection)

            print("Timing...")
            speed = time_model_on_eval_set(tag, eval_items, bm25_index, bm25_chunks, collection)

            print("Scoring with RAGAS (judge: gemma4:26b)...")
            quality = score_model_with_ragas(tag, eval_items, bm25_index, bm25_chunks, collection)

            all_results[label] = {"tag": tag, "speed": speed, "quality": quality}

            print(f"\n  Avg generation:  {speed['avg_generation_ms']:.0f} ms")
            print(f"  Avg tokens/sec:  {speed['avg_tokens_per_sec']:.1f}")
            print(f"  Faithfulness:    {quality['faithfulness']:.4f}")

        except Exception as e:
            print(f"\n  ⚠ {label} FAILED — {e}")
            print(f"  Continuing to next model. Results so far are already saved.")
            all_results[label] = {"tag": tag, "error": str(e)}

        # save after every model, not just at the end — a failure on model 3
        # shouldn't cost you the results from models 1 and 2
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RESULTS_PATH, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"  Results saved to {RESULTS_PATH}")

    return all_results


if __name__ == "__main__":
    import sys
    full_run = "--full" in sys.argv
    limit = None if full_run else 2

    if limit:
        print("SMOKE TEST — 2 questions per model only.")
        print("Pass --full to benchmark all 30.\n")

    run_benchmark(limit=limit)