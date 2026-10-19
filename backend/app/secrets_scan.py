"""Redact likely secrets from source text *before* indexing. Line numbers are preserved."""
import re
from typing import List, Tuple

_PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)")
_TOKENS = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
]
_ASSIGN = re.compile(
    r"""(?i)(?P<k>[\w.-]*(?:api[_-]?key|secret|token|passwd|password|private[_-]?key)[\w.-]*\s*[:=]\s*)"""
    r"""(?P<q>['"])(?P<val>[^'"\s]{8,})(?P=q)""")


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def redact(text: str) -> Tuple[str, List[Tuple[int, str]]]:
    """Return (redacted_text, [(line, kind), ...])."""
    findings: List[Tuple[int, str]] = []

    def keep_lines(m, label):
        findings.append((_line_of(m.string, m.start()), label))
        return "[REDACTED]" + "\n" * m.group(0).count("\n")

    text = _PRIVATE_KEY.sub(lambda m: keep_lines(m, "private key"), text)
    for kind, rx in _TOKENS:
        text = rx.sub(lambda m, k=kind: keep_lines(m, k), text)

    def assign(m):
        findings.append((_line_of(m.string, m.start()), "hard-coded credential"))
        return f"{m.group('k')}{m.group('q')}[REDACTED]{m.group('q')}"

    text = _ASSIGN.sub(assign, text)
    return text, sorted(findings)
