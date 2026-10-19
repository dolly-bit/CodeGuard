# CodeGuard AI

Debugging assistant: bug report + source files -> ranked, line-numbered code evidence, with optional
opt-in AI explanation. Evidence is a **lead, not a verified diagnosis**. Scores are relative, not probabilities.

## What is implemented
**Retrieval (backend, `app/`)**
- BM25 over a code-aware tokenizer (splits `camelCase` / `snake_case`, keeps whole identifiers).
- Syntax-aware chunking: Python via stdlib `ast` (parse only, never executes code); JS/TS, Java, C/C++, C#, Go,
  Rust, PHP, Kotlin, Swift via a **heuristic** declaration splitter (not a real parser); everything else, and any
  parse failure, falls back to line windows. Every result reports which strategy produced it.
- Stack-trace parsing (Python, JS, Java/Kotlin, C#, Go, generic `file:line`) -> boosts for the named file, line range
  and function, weighted toward the innermost frame. Symbols named in the report get a smaller boost.
- Dedup of overlapping chunks and a per-file cap for result diversity.
- Ignore rules (`.git`, `node_modules`, `dist`, binaries, lock files, secret files, `..` paths) and **secret
  redaction** before indexing (line numbers preserved).
- `POST /explain`: opt-in LLM explanation. Requires `consent: true` and `ANTHROPIC_API_KEY`. Code is delimited as
  untrusted data, hypotheses without valid snippet citations are dropped, output is labelled "hypothesis - not verified".
- `POST /feedback` (ids + labels only, never source), request IDs (`X-Request-ID`), structured logs without bodies,
  per-IP rate limiting, CORS allow-list, server-side size limits.

**Frontend (`frontend/`)**: Workik-style workspace; folder and `.zip` upload (ignore rules applied in the browser, zip
bomb guards); syntax-highlighted snippets; language/path/score filters; signal badges; Useful/Irrelevant feedback;
Markdown/JSON export; opt-in browser-only history with delete; keyboard/ARIA improvements.

**Quality**: pytest suite, retrieval evaluation harness (`python -m eval.run_eval`), Vitest tests, ESLint, Docker
Compose, GitHub Actions CI, pinned backend dependencies.

## Not implemented (roadmap)
Tree-sitter parsing, embeddings/semantic search, Git provider integration and incremental indexing, server-side
history/accounts/auth, patch generation, sandboxed test execution, CI/PR integrations. Language support is
extension-based; only Python has real syntax-aware chunking.

## Run locally (Windows PowerShell)
```
cd backend
python -m venv .venv ; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
python -m eval.run_eval
uvicorn app.main:app --reload --port 8000

cd ..\frontend
copy .env.local.example .env.local
npm install
npm run lint ; npm test ; npm run dev
```
Or: `docker compose up --build` (UI :3000, API :8000). To enable AI explanations set `ANTHROPIC_API_KEY` on the backend.

## API
- `GET /health` -> `{status, version, llm_configured}`
- `POST /analyze` `{bug_report, files[{path,content}], top_k 1-20, languages?, path_contains?, min_score?}`
  -> `{mode, notice, files_indexed, chunks_searched, skipped[], warnings[], evidence[]}`
- `POST /explain`, `POST /feedback` (see `app/schemas.py`)

Limits: 10,000 report chars, 300 files, 500 KB/file, 5 MB total. Submitted code is never executed.

## Evaluation (10 self-authored fixture cases; regression harness, not a benchmark)
```
variant                            R@1   R@3   R@5   MRR   avg lines in hit chunk
BM25 + line windows                0.70  1.00  1.00  0.85  11.5
+ syntax-aware chunks              0.70  1.00  1.00  0.85  2.7
+ stack/symbol boosts + dedup      0.90  1.00  1.00  0.95  2.7

Per language (full pipeline):
  Go          R@1 1.00  MRR 1.00
  Java        R@1 1.00  MRR 1.00
  JavaScript  R@1 1.00  MRR 1.00
  Python      R@1 1.00  MRR 1.00
  Rust        R@1 1.00  MRR 1.00
  TypeScript  R@1 0.00  MRR 0.50

Misses (full pipeline): ['ts-lexical']
```
The remaining miss (`ts-lexical`) is a genuine lexical-mismatch case that semantic search would be needed to fix.
