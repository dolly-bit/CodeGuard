from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.retrieval import retrieve_evidence

app = FastAPI(
    title="CodeGuard AI",
    description="Repository-aware debugging assistant — retrieval-first MVP",
    version="0.1.0",
)


class SourceFile(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=500_000)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            raise ValueError("path must be repository-relative and cannot traverse directories")
        return normalized


class AnalyzeRequest(BaseModel):
    bug_report: str = Field(min_length=5, max_length=20_000)
    files: list[SourceFile] = Field(min_length=1, max_length=200)
    top_k: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health():
    return {"status": "ok", "service": "codeguard-ai", "version": "0.1.0"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    if not request.bug_report.strip():
        raise HTTPException(status_code=422, detail="bug_report must not be blank")

    paths = [item.path for item in request.files]
    if len(paths) != len(set(paths)):
        raise HTTPException(status_code=422, detail="duplicate file paths are not allowed")

    evidence = retrieve_evidence(
        bug_report=request.bug_report,
        files=[item.model_dump() for item in request.files],
        top_k=request.top_k,
    )
    return {
        "status": "completed",
        "mode": "retrieval_only",
        "notice": "Ranked evidence is not a verified root-cause diagnosis.",
        "bug_report": request.bug_report,
        "evidence": evidence,
    }
