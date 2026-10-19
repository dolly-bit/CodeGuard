"""Hybrid lexical retrieval: BM25 over code-aware tokens + stack-trace and symbol boosts + dedup.
Scores are relative to the candidate set of one request. They are not probabilities."""
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .chunking import Chunk, chunk_file
from .stacktrace import parse_stack_refs, path_matches
from .tokenizer import tokenize

SCORE_NOTE = "relative retrieval score within this request; not a probability"
W_FILE, W_LINE, W_FUNC, W_SYMBOL = 0.4, 0.4, 0.4, 0.3
MAX_RAW = 1.0 + W_FILE + W_LINE + W_FUNC + W_SYMBOL


@dataclass
class Options:
    syntax: bool = True      # syntax-aware chunking
    boosts: bool = True      # stack-trace + symbol boosts
    dedup: bool = True       # drop overlapping chunks, cap per-file results
    max_per_file: int = 3


@dataclass
class Hit:
    chunk: Chunk
    score: float
    signals: Dict[str, object] = field(default_factory=dict)


def bm25(docs: Sequence[Sequence[str]], query: Sequence[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    n = len(docs)
    if n == 0:
        return []
    avg = (sum(len(d) for d in docs) / n) or 1.0
    tfs = [Counter(d) for d in docs]
    df: Counter = Counter()
    for tf in tfs:
        df.update(tf.keys())
    out = []
    for tf, d in zip(tfs, docs):
        s = 0.0
        for q in query:
            f = tf.get(q, 0)
            if f:
                idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
                s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len(d) / avg))
        out.append(s)
    return out


def _overlap(a: Chunk, b: Chunk) -> float:
    lo, hi = max(a.start_line, b.start_line), min(a.end_line, b.end_line)
    if hi < lo:
        return 0.0
    return (hi - lo + 1) / min(a.end_line - a.start_line + 1, b.end_line - b.start_line + 1)


def search(files: Sequence[Tuple[str, str]], report: str, top_k: int, options: Optional[Options] = None,
           languages: Optional[Sequence[str]] = None, path_contains: Optional[str] = None,
           min_score: float = 0.0) -> Tuple[List[Hit], int]:
    opt = options or Options()
    chunks: List[Chunk] = []
    for path, content in files:
        chunks.extend(chunk_file(path, content, syntax=opt.syntax))
    if languages:
        wanted = {l.lower() for l in languages}
        chunks = [c for c in chunks if c.language.lower() in wanted]
    if path_contains:
        needle = path_contains.lower()
        chunks = [c for c in chunks if needle in c.path.lower()]
    total = len(chunks)
    if not chunks or not report.strip():
        return [], total

    query = sorted(set(tokenize(report)))
    docs = [tokenize(c.content) + tokenize(c.path) + 2 * tokenize(c.symbol or "") for c in chunks]
    lex = bm25(docs, query)
    top = max(lex) or 0.0

    refs = parse_stack_refs(report) if opt.boosts else []
    idents = set(re.findall(r"[A-Za-z_]\w*", report)) if opt.boosts else set()

    hits: List[Hit] = []
    for c, raw_lex in zip(chunks, lex):
        rel = raw_lex / top if top > 0 else 0.0
        f_hit = l_hit = fn_hit = 0.0
        sym_hit = False
        for r in refs:
            if path_matches(c.path, r.file):
                w = 1.0 if r.top else 0.5  # the innermost frame matters most
                f_hit = max(f_hit, w)
                l_hit = max(l_hit, w * bool(r.line and c.start_line <= r.line <= c.end_line))
                fn_hit = max(fn_hit, w * bool(r.func and c.symbol and c.symbol.split(".")[-1] == r.func))
        if opt.boosts and c.symbol:
            last = c.symbol.split(".")[-1]
            sym_hit = len(last) > 2 and last in idents
        raw = rel + W_FILE * f_hit + W_LINE * l_hit + W_FUNC * fn_hit + W_SYMBOL * sym_hit
        score = round(raw / MAX_RAW, 4)
        if score > 0 and score >= min_score:
            hits.append(Hit(c, score, {"lexical": round(rel, 4), "stack_file": f_hit > 0, "stack_line": l_hit > 0,
                                       "stack_function": fn_hit > 0, "symbol_mentioned": sym_hit}))

    hits.sort(key=lambda h: (-h.score, h.chunk.path, h.chunk.start_line))
    if not opt.dedup:
        return hits[:top_k], total
    picked: List[Hit] = []
    per_file: Counter = Counter()
    for h in hits:
        if per_file[h.chunk.path] >= opt.max_per_file:
            continue
        if any(p.chunk.path == h.chunk.path and _overlap(p.chunk, h.chunk) > 0.5 for p in picked):
            continue
        picked.append(h)
        per_file[h.chunk.path] += 1
        if len(picked) >= top_k:
            break
    return picked, total
