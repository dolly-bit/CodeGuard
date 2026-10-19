from ..ignore import filter_files
from ..languages import detect_language  # noqa: F401  (re-exported for convenience)
from ..retrieval import SCORE_NOTE, search
from ..schemas import AnalyzeRequest, AnalyzeResponse, Evidence, Signals, SkippedFile
from ..secrets_scan import redact

NOTICE = ("Retrieval-only result. Ranked snippets are leads for investigation, not a verified diagnosis. "
          "Scores are relative to this request and are not probabilities.")


def run_analysis(req: AnalyzeRequest, request_id: str | None = None) -> AnalyzeResponse:
    kept, skipped = filter_files((f.path, f.content) for f in req.files)
    warnings: list[str] = []
    safe_files = []
    for path, content in kept:
        clean, findings = redact(content)
        if findings:
            kinds = sorted({k for _, k in findings})
            warnings.append(f"{path}: {len(findings)} possible secret(s) redacted ({', '.join(kinds)})")
        safe_files.append((path, clean))
    if skipped:
        warnings.append(f"{len(skipped)} file(s) skipped by ignore rules")

    hits, searched = search(safe_files, req.bug_report, req.top_k, languages=req.languages or None,
                            path_contains=req.path_contains, min_score=req.min_score)
    return AnalyzeResponse(
        notice=NOTICE, request_id=request_id, files_indexed=len(safe_files), chunks_searched=searched,
        skipped=[SkippedFile(path=p, reason=r) for p, r in skipped], warnings=warnings,
        evidence=[Evidence(chunk_id=h.chunk.chunk_id, path=h.chunk.path, language=h.chunk.language,
                           symbol=h.chunk.symbol, chunking=h.chunk.chunking, start_line=h.chunk.start_line,
                           end_line=h.chunk.end_line, content=h.chunk.content, similarity_score=h.score,
                           score_interpretation=SCORE_NOTE, signals=Signals(**h.signals)) for h in hits],
    )
