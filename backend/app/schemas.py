"""Request/response schemas and server-side limits."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from . import config as C


class SourceFile(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=C.MAX_FILE_CHARS)


class AnalyzeRequest(BaseModel):
    bug_report: str = Field(max_length=C.MAX_REPORT_CHARS)
    files: List[SourceFile] = Field(min_length=1, max_length=C.MAX_FILES)
    top_k: int = Field(default=5, ge=C.MIN_TOP_K, le=C.MAX_TOP_K)
    languages: List[str] = Field(default_factory=list, max_length=30)
    path_contains: Optional[str] = Field(default=None, max_length=200)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("bug_report")
    @classmethod
    def report_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("bug_report must not be blank")
        return v

    @model_validator(mode="after")
    def total_size(self):
        total = sum(len(f.content.encode("utf-8")) for f in self.files)
        if total > C.MAX_TOTAL_BYTES:
            raise ValueError(f"total source size exceeds {C.MAX_TOTAL_BYTES} bytes")
        return self


class Signals(BaseModel):
    lexical: float
    stack_file: bool
    stack_line: bool
    stack_function: bool
    symbol_mentioned: bool


class Evidence(BaseModel):
    chunk_id: str
    path: str
    language: str
    symbol: Optional[str] = None
    chunking: str
    start_line: int
    end_line: int
    content: str
    similarity_score: float
    score_interpretation: str
    signals: Signals


class SkippedFile(BaseModel):
    path: str
    reason: str


class AnalyzeResponse(BaseModel):
    mode: Literal["retrieval-only"] = "retrieval-only"
    notice: str
    request_id: Optional[str] = None
    files_indexed: int
    chunks_searched: int
    skipped: List[SkippedFile]
    warnings: List[str]
    evidence: List[Evidence]


# ----- explain (optional, opt-in LLM) -----
class EvidenceIn(BaseModel):
    path: str = Field(max_length=500)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    content: str = Field(max_length=C.MAX_EVIDENCE_CHARS_FOR_LLM)


class ExplainRequest(BaseModel):
    bug_report: str = Field(min_length=1, max_length=C.MAX_REPORT_CHARS)
    evidence: List[EvidenceIn] = Field(min_length=1, max_length=C.MAX_EVIDENCE_FOR_LLM)
    consent: bool = Field(description="User confirmed snippets may be sent to an external provider")


class Hypothesis(BaseModel):
    claim: str
    evidence_ids: List[int]  # 1-based indexes into the evidence list sent
    confidence: Literal["low", "medium", "high"]
    counter_evidence: str = ""


class ExplainResponse(BaseModel):
    label: Literal["hypothesis - not verified"] = "hypothesis - not verified"
    summary: str
    hypotheses: List[Hypothesis]
    next_steps: List[str]
    insufficient_evidence: bool
    model: str


# ----- feedback -----
class FeedbackRequest(BaseModel):
    chunk_id: str = Field(min_length=4, max_length=40)
    path: str = Field(max_length=500)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    label: Literal["useful", "irrelevant"]
    note: Optional[str] = Field(default=None, max_length=300)
