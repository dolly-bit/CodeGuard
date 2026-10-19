"""Append-only JSONL feedback. Stores ids, paths and labels only: never source code."""
import json
import os
import threading
import time

_lock = threading.Lock()


def save_feedback(record: dict, request_id: str | None = None) -> None:
    path = os.getenv("FEEDBACK_PATH", "data/feedback.jsonl")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    line = json.dumps({**record, "ts": time.time(), "request_id": request_id}, ensure_ascii=False)
    with _lock, open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
