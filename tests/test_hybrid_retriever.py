# tests/test_hybrid_retriever.py
import pytest
from src.retrieval.hybrid_retriever import reciprocal_rank_fusion, hybrid_retrieve
from src.retrieval.bm25_index import build_bm25_index


def test_rrf_boosts_chunk_present_in_both_lists():
    bm25_results = [
        {"id": "c1", "text": "one"},
        {"id": "c2", "text": "two"},
    ]
    vector_results = [
        {"id": "c2", "text": "two"},
        {"id": "c3", "text": "three"},
    ]
    fused = reciprocal_rank_fusion(bm25_results, vector_results, k=60)

    ids_in_order = [chunk["id"] for chunk in fused]
    assert ids_in_order == ["c2", "c1", "c3"]

    scores = {chunk["id"]: chunk["rrf_score"] for chunk in fused}
    assert scores["c2"] == pytest.approx(1/62 + 1/61)
    assert scores["c1"] == pytest.approx(1/61)
    assert scores["c3"] == pytest.approx(1/62)


def test_rrf_deduplicates_shared_chunks():
    bm25_results = [{"id": "c1", "text": "one"}]
    vector_results = [{"id": "c1", "text": "one"}]
    fused = reciprocal_rank_fusion(bm25_results, vector_results)

    # c1 appears in both input lists but must appear once in output
    assert len(fused) == 1
    assert fused[0]["id"] == "c1"


class FakeChromaCollection:
    """Stand-in for a real ChromaDB collection — returns fixed results."""
    def query(self, query_embeddings, n_results):
        return {
            "ids": [["c2", "c3"]],
            "documents": [["chunk two text", "chunk three text"]],
            "metadatas": [[{"source": "fake.txt"}, {"source": "fake.txt"}]],
        }


def _fake_embed_fn(text, mode):
    return [0.0, 0.0, 0.0]  # value irrelevant — FakeChromaCollection ignores it


@pytest.fixture
def bm25_setup():
    chunks = [
        {"id": "c1", "text": "one two three"},
        {"id": "c2", "text": "two three four"},
    ]
    index = build_bm25_index(chunks)
    return index, chunks


def test_hybrid_retrieve_respects_top_k(bm25_setup):
    bm25_index, bm25_chunks = bm25_setup
    results = hybrid_retrieve(
        query="two three",
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        chroma_collection=FakeChromaCollection(),
        embed_fn=_fake_embed_fn,
        top_k=1,
    )
    assert len(results) == 1


def test_hybrid_retrieve_fuses_bm25_and_vector_results(bm25_setup):
    bm25_index, bm25_chunks = bm25_setup
    results = hybrid_retrieve(
        query="two three",
        bm25_index=bm25_index,
        bm25_chunks=bm25_chunks,
        chroma_collection=FakeChromaCollection(),
        embed_fn=_fake_embed_fn,
        top_k=5,
    )
    result_ids = {chunk["id"] for chunk in results}
    # c2 comes from both bm25 (real query) and the fake vector collection
    # c1 comes from bm25 only, c3 from the fake vector collection only
    assert "c2" in result_ids
    assert "c3" in result_ids
    # no id duplicated
    assert len(results) == len(result_ids)


def test_rrf_k_controls_score_smoothing():
    # c1 at rank 0, c2 at rank 1 — same list, so there's a real rank gap to smooth
    bm25_results = [
        {"id": "c1", "text": "one"},
        {"id": "c2", "text": "two"},
    ]
    vector_results = []

    fused_small_k = reciprocal_rank_fusion(bm25_results, vector_results, k=1)
    fused_large_k = reciprocal_rank_fusion(bm25_results, vector_results, k=1000)

    scores_small = {c["id"]: c["rrf_score"] for c in fused_small_k}
    scores_large = {c["id"]: c["rrf_score"] for c in fused_large_k}

    gap_small_k = scores_small["c1"] - scores_small["c2"]
    gap_large_k = scores_large["c1"] - scores_large["c2"]

    # small k = rank-1 vs rank-2 matters a lot = big gap
    # large k = rank barely matters = tiny gap
    assert gap_small_k > gap_large_k
    assert gap_large_k == pytest.approx(0, abs=1e-4)