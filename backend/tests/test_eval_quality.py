"""Quality gate: fails if a retrieval change makes the fixture results worse."""
from eval.run_eval import VARIANTS, evaluate, summarize


def test_full_pipeline_beats_or_matches_baseline():
    base = summarize(evaluate(VARIANTS["BM25 + line windows"]))
    full = summarize(evaluate(VARIANTS["+ stack/symbol boosts + dedup"]))
    assert full["mrr"] >= base["mrr"]
    assert full["recall@5"] >= 0.9
    assert full["mrr"] >= 0.8


def test_syntax_chunks_are_more_precise():
    line = summarize(evaluate(VARIANTS["BM25 + line windows"]))
    syn = summarize(evaluate(VARIANTS["+ syntax-aware chunks"]))
    assert syn["mean_hit_lines"] < line["mean_hit_lines"]
