from app.retrieval import Options, search, bm25
from app.tokenizer import tokenize


def test_tokenizer_splits_camel_and_snake():
    t = tokenize("cleanUserName user_name NoneType")
    assert {"clean", "user", "name", "none", "type", "nonetype", "cleanusername"} <= set(t)


def test_bm25_prefers_matching_doc():
    s = bm25([["alpha", "beta"], ["gamma"]], ["alpha"])
    assert s[0] > s[1] == 0


def test_relevant_chunk_ranks_first():
    files = [("math.py", "def add(a, b):\n    return a + b\n"),
             ("text.py", "def normalize(text):\n    return text.strip().lower()\n")]
    hits, total = search(files, "normalize crashes: NoneType has no attribute strip", 5)
    assert hits[0].chunk.path == "text.py" and total >= 2


def test_no_overlap_gives_no_hits():
    assert search([("a.py", "def foo():\n    pass\n")], "zzz qqq", 5)[0] == []


def test_blank_report_or_no_chunks():
    assert search([("a.py", "x = 1")], "  ", 5) == ([], 1)
    assert search([("a.py", "")], "x", 5) == ([], 0)


def test_stack_trace_boost_beats_lexical_distractor():
    files = [("a/target.py", "def run():\n    return 1\n"),
             ("b/noise.py", "def other():\n    # keyerror country rate report\n    return 2\n")]
    report = 'File "a/target.py", line 2, in run\nKeyError: country rate report'
    hits, _ = search(files, report, 3)
    assert hits[0].chunk.path == "a/target.py" and hits[0].signals["stack_line"]


def test_top_k_and_filters():
    files = [(f"m{i}.py", f"def foo{i}():\n    return 'target word'\n") for i in range(6)] + [("x.js", "function foo(){ return 'target word'; }")]
    assert len(search(files, "target word", 2)[0]) == 2
    assert all(h.chunk.language == "JavaScript" for h in search(files, "target word", 5, languages=["javascript"])[0])
    assert all("m3" in h.chunk.path for h in search(files, "target word", 5, path_contains="m3")[0])
    assert all(h.score >= 0.999 for h in search(files, "target word", 5, min_score=0.999)[0])


def test_per_file_cap_adds_diversity():
    text = "\n".join(f"value = compute(item{i})  # target token" for i in range(100))
    opt = lambda **kw: Options(syntax=False, boosts=False, **kw)
    assert len(search([("a.txt", text)], "target token", 5, opt(dedup=False))[0]) == 3
    assert len(search([("a.txt", text)], "target token", 5, opt(dedup=True, max_per_file=1))[0]) == 1


def test_overlapping_chunks_are_dropped():
    from app.chunking import Chunk
    from app.retrieval import _overlap
    a, b = Chunk("f", 1, 40, "x"), Chunk("f", 10, 50, "y")
    assert _overlap(a, b) > 0.5 and _overlap(a, Chunk("f", 41, 60, "z")) == 0


def test_deterministic_ties():
    files = [("b.py", "def f():\n    return 'same'\n"), ("a.py", "def f():\n    return 'same'\n")]
    assert [h.chunk.path for h in search(files, "same", 5)[0]] == ["a.py", "b.py"]
