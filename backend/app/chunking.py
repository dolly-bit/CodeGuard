"""Chunking. Python uses the stdlib `ast` module (parse only, never executes code).
Brace languages use a heuristic declaration splitter. Everything else falls back to line windows.
The `chunking` field on each Chunk says which strategy actually produced it."""
import ast
import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .languages import BRACE_LANGUAGES, detect_language

MAX_LINES = 80
WINDOW = 40
OVERLAP = 8


@dataclass(frozen=True)
class Chunk:
    path: str
    start_line: int  # 1-based inclusive
    end_line: int
    content: str
    language: str = "Text"
    symbol: Optional[str] = None
    chunking: str = "lines"

    @property
    def chunk_id(self) -> str:
        raw = f"{self.path}:{self.start_line}:{self.end_line}:{self.content}"
        return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:12]


def _windows(path, lines, first, language, symbol, chunking, size=WINDOW, overlap=OVERLAP) -> List[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("require size > 0 and 0 <= overlap < size")
    out, step = [], size - overlap
    for s in range(0, len(lines), step):
        w = lines[s:s + size]
        body = "\n".join(w)
        if body.strip():
            out.append(Chunk(path, first + s, first + s + len(w) - 1, body, language, symbol, chunking))
        if s + size >= len(lines):
            break
    return out


def _segment(path, lines, start, end, language, symbol, chunking) -> List[Chunk]:
    while end >= start and not lines[end - 1].strip():
        end -= 1
    if end < start:
        return []
    seg = lines[start - 1:end]
    if len(seg) <= MAX_LINES:
        body = "\n".join(seg)
        return [Chunk(path, start, end, body, language, symbol, chunking)] if body.strip() else []
    return _windows(path, seg, start, language, symbol, chunking)


Span = Tuple[int, int, Optional[str]]


def _assemble(path, lines, spans: List[Span], language, chunking) -> List[Chunk]:
    out, cursor = [], 1
    for s, e, sym in sorted(spans, key=lambda x: x[0]):
        if s < cursor:  # overlapping span; skip defensively
            continue
        if s > cursor:
            out += _segment(path, lines, cursor, s - 1, language, None, chunking)
        out += _segment(path, lines, s, e, language, sym, chunking)
        cursor = e + 1
    if cursor <= len(lines):
        out += _segment(path, lines, cursor, len(lines), language, None, chunking)
    return out


# ---------- Python (ast) ----------
def _py_start(node) -> int:
    return min([node.lineno] + [d.lineno for d in node.decorator_list])


def _python_spans(tree: ast.Module) -> List[Span]:
    spans: List[Span] = []
    funcs = (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in tree.body:
        if isinstance(node, funcs):
            spans.append((_py_start(node), node.end_lineno, node.name))
        elif isinstance(node, ast.ClassDef):
            s, e = _py_start(node), node.end_lineno
            if e - s + 1 <= MAX_LINES:
                spans.append((s, e, node.name))
                continue
            cur = s
            for m in (n for n in node.body if isinstance(n, funcs)):
                ms = _py_start(m)
                if ms > cur:
                    spans.append((cur, ms - 1, node.name))
                spans.append((ms, m.end_lineno, f"{node.name}.{m.name}"))
                cur = m.end_lineno + 1
            if cur <= e:
                spans.append((cur, e, node.name))
    return spans


# ---------- Brace languages (heuristic) ----------
_MOD = (r"(?:(?:export|default|public|private|protected|internal|static|final|abstract|override|virtual|"
        r"async|suspend|open|inline|sealed|data|unsafe|extern|pub(?:\([^)]*\))?)\s+)*")
_CLASS = re.compile(r"^\s*" + _MOD + r"(?:class|interface|enum|struct|trait|impl|object|type)\s+(\w+)")
_FN_KW = re.compile(r"^\s*" + _MOD + r"(?:function|fun|func|fn|def)\s*\*?\s*(?:\([^)]*\)\s*)?(\w+)")
_ARROW = re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=]+)?=\s*(?:async\s*)?"
                    r"(?:\([^)]*\)|\w+)\s*(?::\s*[\w<>\[\]|, ]+)?\s*=>")
_TYPED = re.compile(r"^\s*" + _MOD + r"(?:[\w<>\[\],.?*&:]+\s+)+\**(\w+)\s*\([^;]*$")
_JSMETHOD = re.compile(r"^\s{2,}(?:async\s+)?(?:static\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\{\s*$")
_CONTROL = {"if", "for", "while", "switch", "catch", "return", "else", "new", "throw", "sizeof", "do",
            "try", "function", "typeof", "await", "yield", "case", "using", "foreach", "elif"}
_COMMENT_START = ("//", "/*", "*", "@", "#[", "///")


def _brace_spans(lines: List[str]) -> List[Span]:
    starts = []  # (line_idx, symbol, indent, is_class)
    for i, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith(_COMMENT_START):
            continue
        first = line.split()[0].rstrip("(") if line.split() else ""
        if first in _CONTROL:
            continue
        indent = len(line) - len(line.lstrip())
        m = _CLASS.match(line)
        if m:
            starts.append((i, m.group(1), indent, True))
            continue
        for rx in (_FN_KW, _ARROW, _TYPED, _JSMETHOD):
            m = rx.match(line)
            if m and m.group(1) not in _CONTROL:
                starts.append((i, m.group(1), indent, False))
                break
    if not starts:
        return []
    spans, cur_class, begins = [], None, []
    for k, (i, name, indent, is_class) in enumerate(starts):
        if is_class:
            cur_class, symbol = (indent, name), name
        elif cur_class and indent > cur_class[0]:
            symbol = f"{cur_class[1]}.{name}"
        else:
            cur_class, symbol = None, name
        j = i - 1  # absorb leading comments/annotations
        floor = starts[k - 1][0] if k else -1
        while j > floor and lines[j].strip() and lines[j].lstrip().startswith(_COMMENT_START):
            j -= 1
        begins.append((j + 1, symbol))
    for k, (b, symbol) in enumerate(begins):
        end = (begins[k + 1][0] if k + 1 < len(begins) else len(lines))  # exclusive, 0-based
        spans.append((b + 1, end, symbol))
    return spans


def chunk_file(path: str, text: str, language: Optional[str] = None, syntax: bool = True) -> List[Chunk]:
    language = language or detect_language(path)
    lines = text.splitlines()
    if not any(l.strip() for l in lines):
        return []
    if syntax and language == "Python":
        try:
            spans = _python_spans(ast.parse(text))
            if spans:
                return _assemble(path, lines, spans, language, "python-ast")
        except Exception:  # SyntaxError, ValueError, RecursionError...
            pass
    elif syntax and language in BRACE_LANGUAGES:
        spans = _brace_spans(lines)
        if spans:
            return _assemble(path, lines, spans, language, "heuristic-brace")
    return _windows(path, lines, 1, language, None, "lines")
