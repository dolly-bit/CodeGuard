"""Code-aware tokenizer: splits camelCase / snake_case and keeps the whole identifier too."""
import re

_WORD = re.compile(r"[A-Za-z0-9]+")
_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
STOP = frozenset("""the an is are was were when if in of to and or it this that with for on at be as by from
but my we file line traceback most recent call last at""".split())


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for word in _WORD.findall(text):
        out.append(word.lower())
        parts = [p.lower() for p in _CAMEL.findall(word)]
        if len(parts) > 1:
            out.extend(parts)
    return [t for t in out if len(t) > 1 and t not in STOP]
