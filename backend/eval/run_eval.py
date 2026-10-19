"""Run: python -m eval.run_eval   (from backend/). Compares retrieval variants on the fixture cases."""
from collections import defaultdict

from app.retrieval import Options, search
from .cases import CASES, target_of

VARIANTS = {
    "BM25 + line windows": Options(syntax=False, boosts=False, dedup=False),
    "+ syntax-aware chunks": Options(syntax=True, boosts=False, dedup=False),
    "+ stack/symbol boosts + dedup": Options(syntax=True, boosts=True, dedup=True),
}


def evaluate(options: Options, k_max: int = 5):
    rows = []
    for case in CASES:
        path, line = target_of(case)
        hits, _ = search(list(case["files"].items()), case["report"], k_max, options)
        rank, size = None, None
        for i, h in enumerate(hits, 1):
            c = h.chunk
            if c.path == path and c.start_line <= line <= c.end_line:
                rank, size = i, c.end_line - c.start_line + 1
                break
        rows.append({"id": case["id"], "language": case["language"], "rank": rank, "size": size})
    return rows


def summarize(rows):
    n = len(rows)
    r = lambda k: sum(1 for x in rows if x["rank"] and x["rank"] <= k) / n
    mrr = sum(1 / x["rank"] for x in rows if x["rank"]) / n
    sizes = [x["size"] for x in rows if x["size"]]
    return {"recall@1": r(1), "recall@3": r(3), "recall@5": r(5), "mrr": mrr,
            "mean_hit_lines": sum(sizes) / len(sizes) if sizes else 0.0}


def per_language(rows):
    g = defaultdict(list)
    for x in rows:
        g[x["language"]].append(x)
    return {lang: summarize(v) for lang, v in g.items()}


if __name__ == "__main__":
    print(f"{'variant':34} R@1   R@3   R@5   MRR   avg lines in hit chunk")
    for name, opt in VARIANTS.items():
        s = summarize(evaluate(opt))
        print(f"{name:34} {s['recall@1']:.2f}  {s['recall@3']:.2f}  {s['recall@5']:.2f}  {s['mrr']:.2f}  {s['mean_hit_lines']:.1f}")
    print("\nPer language (full pipeline):")
    full = evaluate(VARIANTS["+ stack/symbol boosts + dedup"])
    for lang, s in sorted(per_language(full).items()):
        print(f"  {lang:11} R@1 {s['recall@1']:.2f}  MRR {s['mrr']:.2f}")
    print("\nMisses (full pipeline):", [x["id"] for x in full if not x["rank"] or x["rank"] > 1] or "none")
    print("NOTE: 10 self-authored cases; a regression harness, not evidence of real-world accuracy.")
