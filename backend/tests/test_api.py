import json

from fastapi.testclient import TestClient

from app import llm, main
from app.main import app
from app.ratelimit import SlidingWindowLimiter

client = TestClient(app)
FILE = {"path": "app/utils/text.py", "content": "def normalize(text):\n    return text.strip().lower()\n"}


def post(**over):
    body = {"bug_report": "normalize fails: NoneType has no attribute strip", "files": [FILE], "top_k": 3}
    body.update(over)
    return client.post("/analyze", json=body)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    assert "x-request-id" in r.headers


def test_analyze_returns_evidence_and_metadata():
    r = post()
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "retrieval-only" and body["files_indexed"] == 1
    ev = body["evidence"][0]
    assert {"chunk_id", "path", "language", "symbol", "chunking", "start_line", "end_line", "content",
            "similarity_score", "score_interpretation", "signals"} <= ev.keys()
    assert ev["symbol"] == "normalize" and ev["chunking"] == "python-ast"


def test_validation_errors():
    assert post(bug_report="  ").status_code == 422
    assert post(files=[]).status_code == 422
    assert post(top_k=999).status_code == 422
    assert post(min_score=2).status_code == 422


def test_ignored_files_and_secret_redaction():
    secret = {"path": "app/cfg.py", "content": 'password = "supersecret123"\ndef normalize(): pass\n'}
    r = post(files=[FILE, secret, {"path": "node_modules/x.js", "content": "normalize"}])
    body = r.json()
    assert body["skipped"][0]["reason"] == "ignored folder"
    assert any("redacted" in w for w in body["warnings"])
    assert "supersecret123" not in json.dumps(body)


def test_filters():
    other = {"path": "b.js", "content": "function normalize(t){ return t; }"}
    r = post(files=[FILE, other], languages=["JavaScript"])
    assert {e["language"] for e in r.json()["evidence"]} == {"JavaScript"}


def test_explain_requires_consent_and_provider():
    base = {"bug_report": "x", "evidence": [{"path": "a.py", "start_line": 1, "end_line": 1, "content": "x"}]}
    assert client.post("/explain", json={**base, "consent": False}).status_code == 400
    app.dependency_overrides[llm.get_provider] = lambda: None
    try:
        assert client.post("/explain", json={**base, "consent": True}).status_code == 503

        class Fake:
            model = "fake"
            def complete(self, s, u):
                return json.dumps({"summary": "s", "hypotheses": [{"claim": "c", "evidence_ids": [1], "confidence": "low"}], "next_steps": []})
        app.dependency_overrides[llm.get_provider] = lambda: Fake()
        r = client.post("/explain", json={**base, "consent": True})
        assert r.status_code == 200 and r.json()["hypotheses"][0]["evidence_ids"] == [1]
    finally:
        app.dependency_overrides.clear()


def test_feedback_stores_no_source(tmp_path, monkeypatch):
    path = tmp_path / "fb.jsonl"
    monkeypatch.setenv("FEEDBACK_PATH", str(path))
    r = client.post("/feedback", json={"chunk_id": "abcd1234", "path": "a.py", "start_line": 1, "end_line": 2, "label": "useful"})
    assert r.status_code == 204
    rec = json.loads(path.read_text().splitlines()[0])
    assert rec["label"] == "useful" and "content" not in rec


def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr(main, "limiter", SlidingWindowLimiter(1, 60))
    assert post().status_code == 200
    r = post()
    assert r.status_code == 429 and "retry-after" in r.headers
