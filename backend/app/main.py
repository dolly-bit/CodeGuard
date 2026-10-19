import logging
import os
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import llm
from .feedback_store import save_feedback
from .ratelimit import SlidingWindowLimiter
from .schemas import (AnalyzeRequest, AnalyzeResponse, ExplainRequest, ExplainResponse, FeedbackRequest)
from .services.analysis_service import run_analysis

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("codeguard")

app = FastAPI(title="CodeGuard AI", version="0.2.0")
limiter = SlidingWindowLimiter(int(os.getenv("RATE_LIMIT_PER_MIN", "60")), 60)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    request.state.request_id = rid
    if request.method == "POST":
        ok, retry = limiter.check(request.client.host if request.client else "unknown")
        if not ok:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again shortly.",
                                                          "request_id": rid},
                                headers={"Retry-After": str(retry), "X-Request-ID": rid})
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    # Safe metadata only: never bodies, never source code.
    log.info("rid=%s %s %s -> %s %.0fms", rid, request.method, request.url.path, response.status_code,
             (time.perf_counter() - start) * 1000)
    return response


# Added last so it is the outermost middleware (CORS headers also appear on 429s).
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
           if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"], expose_headers=["X-Request-ID"])


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version, "llm_configured": llm.get_provider() is not None}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, request: Request):
    return run_analysis(req, request.state.request_id)


@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest, provider=Depends(llm.get_provider)):
    if not req.consent:
        raise HTTPException(status_code=400, detail="Consent is required before snippets are sent to an AI provider.")
    if provider is None:
        raise HTTPException(status_code=503, detail="AI explanation is not configured on this server.")
    try:
        return llm.explain(req, provider)
    except Exception:
        raise HTTPException(status_code=502, detail="The AI provider request failed.")


@app.post("/feedback", status_code=204)
def feedback(req: FeedbackRequest, request: Request):
    save_feedback(req.model_dump(), request.state.request_id)


@app.exception_handler(Exception)
async def unexpected(request: Request, exc: Exception):
    rid = getattr(request.state, "request_id", uuid.uuid4().hex[:12])
    log.exception("rid=%s unhandled error", rid)
    return JSONResponse(status_code=500, content={"detail": "Internal error", "request_id": rid})
