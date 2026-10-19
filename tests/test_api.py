from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_returns_line_numbered_evidence():
    response = client.post("/analyze", json={
        "bug_report": "AttributeError accessing user.email when user is missing",
        "top_k": 2,
        "files": [
            {"path": "app/routes/users.py", "content": "def get_email(user):\n    return user.email\n"},
            {"path": "app/utils/text.py", "content": "def normalize(text):\n    return text.strip().lower()\n"},
        ],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "retrieval_only"
    assert len(body["evidence"]) <= 2
    assert all("start_line" in item and "end_line" in item for item in body["evidence"])
    assert body["evidence"][0]["path"] == "app/routes/users.py"


def test_rejects_path_traversal():
    response = client.post("/analyze", json={
        "bug_report": "This bug report is long enough",
        "files": [{"path": "../secrets.env", "content": "SECRET=x"}],
    })
    assert response.status_code == 422


def test_rejects_duplicate_paths():
    response = client.post("/analyze", json={
        "bug_report": "This bug report is long enough",
        "files": [
            {"path": "app.py", "content": "x = 1"},
            {"path": "app.py", "content": "x = 2"},
        ],
    })
    assert response.status_code == 422
