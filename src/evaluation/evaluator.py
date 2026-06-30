"""
evaluator.py — Score the RAG pipeline using RAGAS metrics.

Loads eval_set.json, runs each question through the full pipeline,
then scores faithfulness, answer relevancy, context precision, and recall.
Results are printed to terminal and saved to eval_results.json.
"""

import json
import time
from pathlib import Path

from datasets import Dataset
from langchain_community.llms import Ollama
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings.base import BaseRagasEmbeddings
from ragas.run_config import RunConfig
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

from src.generation.query_pipeline import load_indexes, query as run_query
from src.ingestion.embedder import embed_text as local_embed_text

# ── paths ──────────────────────────────────────────────────────────────────────
EVAL_SET_PATH = Path("src/evaluation/eval_set.json")
RESULTS_PATH  = Path("src/evaluation/eval_results.json")

# ── model used as the RAGAS judge ──────────────────────────────────────────────
JUDGE_MODEL = "gemma4:26b"


# ── Section 2: Ollama LLM wrapper for RAGAS ───────────────────────────────────

def build_ragas_llm() -> LangchainLLMWrapper: # type: ignore
    """
    Wrap the local Ollama model so RAGAS can use it as a judge.

    RAGAS needs an LLM to score metrics like faithfulness — it asks the model
    questions like "is this claim supported by this context?". By default RAGAS
    expects OpenAI. This wrapper points it at your local Ollama model instead.

    Returns:
        A LangchainLLMWrapper around the local Ollama model.
    """
    ollama_llm = Ollama(model=JUDGE_MODEL, temperature=0)  # temp=0 for consistent scoring
    return LangchainLLMWrapper(ollama_llm)


# ── Section 2b: Ollama embeddings wrapper for RAGAS ──────────────────────────────

class LocalEmbeddings(BaseRagasEmbeddings):
    """
    Wrap the local nomic-embed-text model so RAGAS can use it for scoring.

    RAGAS uses embeddings when computing answer_relevancy — it embeds the
    question and the answer then measures how close they are in vector space.
    By default it tries to use OpenAI embeddings. This class points it at
    your local Ollama embedder instead.

    Implements the two methods langchain's Embeddings ABC requires:
      - embed_documents: embed a list of texts (used for context chunks)
      - embed_query:     embed a single query string
    """

    run_config: RunConfig = RunConfig()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document strings. Returns a list of vectors."""
        return [local_embed_text(text, mode="document") for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string. Returns one vector."""
        return local_embed_text(text, mode="query")

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async version — delegates to the sync implementation."""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Async version — delegates to the sync implementation."""
        return self.embed_query(text)


# ── Section 3: load eval set ───────────────────────────────────────────────────

def load_eval_set(path: Path = EVAL_SET_PATH) -> list[dict]:
    """
    Read eval_set.json and return the list of Q&A pairs.

    Args:
        path: Path to eval_set.json.
    Returns:
        List of dicts, each with 'question', 'ground_truth', 'source_document'.
    """
    with open(path) as f:
        return json.load(f)


# ── Section 4: run pipeline for one question ──────────────────────────────────

def run_pipeline_for_question(
    question: str,
    bm25_index,
    bm25_chunks: list[dict],
    collection,
) -> dict:
    """
    Run one question through the full RAG pipeline and return what RAGAS needs.

    RAGAS requires: the answer text, and the actual text of each retrieved chunk
    (not just the chunk IDs — it needs to read the content to score faithfulness).

    Args:
        question:    The question string to run.
        bm25_index:  Loaded BM25 index.
        bm25_chunks: Chunks associated with the BM25 index.
        collection:  ChromaDB collection.
    Returns:
        Dict with 'answer' (str) and 'contexts' (list of chunk text strings).
    """
    result = run_query(
        question=question,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        collection=collection,
    )

    # RAGAS needs chunk text, not chunk IDs — pull text from chunks_used
    # chunks_used is a list of IDs; we need to find matching text in bm25_chunks
    chunks_used_ids = set(result["chunks_used"])
    context_texts = [
        c["text"] for c in bm25_chunks if c["id"] in chunks_used_ids
    ]

    return {
        "answer":   result["answer"],
        "contexts": context_texts,
    }


# ── Section 5: build the RAGAS dataset ────────────────────────────────────────

def build_ragas_dataset(
    eval_items: list[dict],
    bm25_index,
    bm25_chunks: list[dict],
    collection,
    limit: int | None = None,
) -> Dataset:
    """
    Run the pipeline for every eval question and assemble a RAGAS Dataset.

    RAGAS expects a HuggingFace Dataset with four columns:
      - question:      the question asked
      - answer:        what the pipeline returned
      - contexts:      list of retrieved chunk texts
      - ground_truth:  the correct answer from eval_set.json

    Args:
        eval_items:  List of eval Q&A dicts from eval_set.json.
        bm25_index:  Loaded BM25 index.
        bm25_chunks: Chunks for BM25.
        collection:  ChromaDB collection.
        limit:       If set, only run the first N questions (used for smoke test).
    Returns:
        A HuggingFace Dataset ready for ragas.evaluate().
    """
    if limit:
        eval_items = eval_items[:limit]

    questions, answers, contexts, ground_truths = [], [], [], []

    for i, item in enumerate(eval_items, 1):
        print(f"  [{i}/{len(eval_items)}] {item['question'][:70]}...")
        try:
            pipeline_result = run_pipeline_for_question(
                question=item["question"],
                bm25_index=bm25_index,
                bm25_chunks=bm25_chunks,
                collection=collection,
            )
            questions.append(item["question"])
            answers.append(pipeline_result["answer"])
            contexts.append(pipeline_result["contexts"])
            ground_truths.append(item["ground_truth"])
        except Exception as e:
            # log and skip rather than crash the whole run
            print(f"    ⚠ Skipped (error): {e}")

    return Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths,
    })


# ── Section 6: run RAGAS and save results ─────────────────────────────────────

def evaluate_pipeline(limit: int | None = None) -> dict:
    """
    Full evaluation run: load indexes, run pipeline, score with RAGAS, save results.

    Args:
        limit: If set, only evaluate the first N questions. Used for smoke tests.
    Returns:
        Dict of metric name → score.
    """
    print("Loading indexes...")
    bm25_index, bm25_chunks, collection = load_indexes()
    print("Indexes loaded.\n")

    print("Loading eval set...")
    eval_items = load_eval_set()
    total = limit or len(eval_items)
    print(f"Running {total} questions through pipeline...\n")

    ragas_llm = build_ragas_llm()

    # attach the local judge LLM to each metric
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm

    start = time.time()
    dataset = build_ragas_dataset(
        eval_items=eval_items,
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        collection=collection,
        limit=limit,
    )
    elapsed_pipeline = time.time() - start

    print(f"\nPipeline calls done in {elapsed_pipeline:.1f}s. Running RAGAS scoring...\n")

    start = time.time()
    run_config = RunConfig(
        timeout=300,   # 5 min per LLM call — faithfulness makes 2 chained calls per question
        max_retries=2,
        max_workers=1, # sequential — Ollama can't handle parallel requests
    )
    result = evaluate(
        dataset,
        metrics=metrics,
        embeddings=LocalEmbeddings(),
        run_config=run_config,
    )
    elapsed_ragas = time.time() - start

    import math

    def _mean(values) -> float:
        # result[metric] is a list of per-question scores — average them.
        # RAGAS uses np.nan (not None) for failed/timed-out scores, so we
        # must filter both None and NaN or one bad value poisons the average.
        vals = [v for v in values if v is not None and not math.isnan(v)]
        skipped = len(values) - len(vals)
        if skipped:
            print(f"    ⚠ {skipped} question(s) had no valid score for this metric — excluded from average")
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    scores = {
        "faithfulness":       _mean(result["faithfulness"]),
        "answer_relevancy":   _mean(result["answer_relevancy"]),
        "context_precision":  _mean(result["context_precision"]),
        "context_recall":     _mean(result["context_recall"]),
    }

    # ── print results ──────────────────────────────────────────────────────────
    print("=" * 50)
    print("RAGAS EVALUATION RESULTS")
    print("=" * 50)
    for metric, score in scores.items():
        status = "✅" if metric != "faithfulness" else ("✅" if score >= 0.75 else "❌ BELOW THRESHOLD")
        print(f"  {metric:<25} {score:.4f}  {status}")
    print("=" * 50)
    print(f"Questions evaluated: {len(dataset)}")
    print(f"Pipeline time:       {elapsed_pipeline:.1f}s")
    print(f"RAGAS scoring time:  {elapsed_ragas:.1f}s")

    # ── save results ───────────────────────────────────────────────────────────
    output = {
        "scores":               scores,
        "questions_evaluated":  len(dataset),
        "pipeline_time_s":      round(elapsed_pipeline, 1),
        "ragas_time_s":         round(elapsed_ragas, 1),
        "judge_model":          JUDGE_MODEL,
        "faithfulness_passed":  scores["faithfulness"] >= 0.75,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {RESULTS_PATH}")

    return scores


# ── Section 7: smoke test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # pass --full to run all 20 questions; default is 2 for a quick smoke test
    full_run = "--full" in sys.argv
    limit = None if full_run else 2

    if limit:
        print("SMOKE TEST — running 2 questions only.")
        print("Pass --full to evaluate all 20.\n")

    evaluate_pipeline(limit=limit)