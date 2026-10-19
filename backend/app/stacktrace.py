"""Extract file/line/function references from pasted stack traces (Python, JS, Java/Kotlin, C#, Go, generic)."""
import re
from dataclasses import dataclass, replace
from typing import List, Optional

from .languages import EXT


@dataclass(frozen=True)
class StackRef:
    file: str
    line: Optional[int] = None
    func: Optional[str] = None
    top: bool = False  # innermost frame (where the error was raised)


_PY = re.compile(r'File "([^"]+)", line (\d+)(?:, in ([\w<>.]+))?')
_JAVA = re.compile(r"\bat\s+([\w$.]+)\(([\w$]+\.(?:java|kt|scala))(?::(\d+))?\)")
_CS = re.compile(r"\bat\s+([\w.<>$]+)\(.*?\)\s+in\s+(.+?):line\s+(\d+)")
_JS = re.compile(r"\bat\s+(?:(?:async\s+)?([\w$.<>]+)\s+\()?((?:[A-Za-z]:)?[^\s():]+?\.\w{1,5}):(\d+)(?::\d+)?\)?")
_GENERIC = re.compile(r"((?:[\w.\-]+[/\\])*[\w.\-]+\.([A-Za-z]{1,5})):(\d+)")


def _last(name: Optional[str]) -> Optional[str]:
    if not name or name.startswith("<"):
        return None
    return re.split(r"[.$]", name)[-1] or None


def parse_stack_refs(report: str) -> List[StackRef]:
    found = []  # (position, is_python_style, ref)
    for m in _PY.finditer(report):
        found.append((m.start(), True, StackRef(m.group(1), int(m.group(2)), _last(m.group(3)))))
    for m in _JAVA.finditer(report):
        found.append((m.start(), False, StackRef(m.group(2), int(m.group(3)) if m.group(3) else None, _last(m.group(1)))))
    for m in _CS.finditer(report):
        found.append((m.start(), False, StackRef(m.group(2), int(m.group(3)), _last(m.group(1)))))
    for m in _JS.finditer(report):
        if m.group(2).split(".")[-1].lower() in EXT:
            found.append((m.start(), False, StackRef(m.group(2), int(m.group(3)), _last(m.group(1)))))
    for m in _GENERIC.finditer(report):
        if m.group(2).lower() in EXT:
            found.append((m.start(), False, StackRef(m.group(1), int(m.group(3)))))
    found.sort(key=lambda t: t[0])
    best: dict = {}
    for pos, py, r in found:  # same file+line seen by several patterns: keep the one with a function name
        key = (r.file.replace("\\", "/").rsplit("/", 1)[-1].lower(), r.line)
        if key not in best or (r.func and not best[key][2].func):
            best[key] = (pos, py, r)
    items = sorted(best.values(), key=lambda t: t[0])
    if not items:
        return []
    # Python prints the innermost frame last; JS/Java/C#/Go print it first.
    top_idx = len(items) - 1 if any(py for _, py, _ in items) else 0
    return [replace(r, top=(i == top_idx)) for i, (_, _, r) in enumerate(items)]


def _norm(p: str) -> str:
    p = p.replace("\\", "/").lower()
    return p[2:] if p.startswith("./") else p


def path_matches(chunk_path: str, ref_file: str) -> bool:
    a, b = _norm(chunk_path), _norm(ref_file)
    if a == b or b.endswith("/" + a) or a.endswith("/" + b):
        return True
    return "/" not in b and a.rsplit("/", 1)[-1] == b
