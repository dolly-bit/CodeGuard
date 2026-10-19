# CodeGuard AI — Starter MVP

Repository-aware debugging assistant. This starter implements deterministic code retrieval with TF-IDF, a FastAPI endpoint, and tests. It does **not** claim an LLM diagnosis is verified; the first milestone focuses on retrieval quality and a clean API contract.

## MVP flow
1. Submit a bug report / stack trace and repository files.
2. Split source files into line-numbered chunks.
3. Rank chunks by TF-IDF similarity to the bug report.
4. Return evidence with paths, line ranges, and scores.
5. Later milestones add Git repository ingestion, LLM explanations, patch proposals, and isolated test execution.

## Requirements
- Python 3.11+
- Git (optional for later repo-cloning milestone)

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs.

## Test
```bash
pytest -q
```

## Example request
```bash
curl -X POST http://127.0.0.1:8000/analyze \\
  -H "Content-Type: application/json" \\
  -d '{
    "bug_report": "API returns 500 when user is missing. AttributeError accessing user.email",
    "top_k": 3,
    "files": [
      {"path": "app/routes/users.py", "content": "def get_email(user):\\n    return user.email\\n"},
      {"path": "app/utils/text.py", "content": "def normalize(text):\\n    return text.strip().lower()\\n"}
    ]
  }'
```

## Security notes
- This version accepts source text directly; it does not clone arbitrary URLs or execute submitted code.
- Do not upload secrets, `.env` files, private keys, credentials, or proprietary code without authorization.
- Never execute suggested patches against production systems.
- Future test execution must use an isolated, resource-limited container with network access disabled by default.

## Known limitations
- TF-IDF is a retrieval baseline, not semantic understanding.
- Ranking scores are relative similarity scores, not probabilities of correctness.
- A high-ranked snippet is not proof of root cause.
- There is no repository indexing persistence, auth, LLM, patch application, or sandbox execution yet.
