import type { AnalyzeResponse, Evidence, ExplainResponse, FeedbackLabel, SourceFile } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function checkHealth(): Promise<{ online: boolean; llm: boolean }> {
  try {
    const r = await fetch(`${API_URL}/health`, { cache: "no-store" });
    if (!r.ok) return { online: false, llm: false };
    const j = await r.json().catch(() => ({}));
    return { online: true, llm: !!j.llm_configured };
  } catch {
    return { online: false, llm: false };
  }
}

function isAnalyzeResponse(x: unknown): x is AnalyzeResponse {
  const d = x as AnalyzeResponse;
  return !!d && Array.isArray(d.evidence) && typeof d.notice === "string" && Array.isArray(d.warnings) &&
    Array.isArray(d.skipped) &&
    d.evidence.every((e) => typeof e.path === "string" && typeof e.similarity_score === "number" && !!e.signals);
}

async function post(path: string, body: unknown): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
  } catch {
    throw new Error(`Cannot reach the backend at ${API_URL}. Check that FastAPI is running and CORS allows this origin.`);
  }
  if (res.ok) return res;
  let detail = `Request failed (HTTP ${res.status}).`;
  try {
    const j = await res.json();
    if (typeof j.detail === "string") detail = j.detail;
    else if (Array.isArray(j.detail)) detail = j.detail.map((d: { msg: string }) => d.msg).join("; ");
  } catch { /* keep default */ }
  if (res.status === 429) detail += ` Retry in ${res.headers.get("Retry-After") ?? "a few"} seconds.`;
  const rid = res.headers.get("X-Request-ID");
  throw new Error(rid ? `${detail} (ref ${rid})` : detail);
}

export async function analyze(bug_report: string, files: SourceFile[], top_k: number): Promise<AnalyzeResponse> {
  const data: unknown = await (await post("/analyze", { bug_report, files, top_k })).json();
  if (!isAnalyzeResponse(data)) throw new Error("The backend returned an unexpected response format.");
  return data;
}

export async function explain(bug_report: string, evidence: Evidence[], consent: boolean): Promise<ExplainResponse> {
  const res = await post("/explain", {
    bug_report, consent,
    evidence: evidence.map((e) => ({ path: e.path, start_line: e.start_line, end_line: e.end_line, content: e.content })),
  });
  const d = (await res.json()) as ExplainResponse;
  if (!d || !Array.isArray(d.hypotheses)) throw new Error("The backend returned an unexpected response format.");
  return d;
}

export async function sendFeedback(ev: Evidence, label: FeedbackLabel): Promise<void> {
  await post("/feedback", { chunk_id: ev.chunk_id, path: ev.path, start_line: ev.start_line, end_line: ev.end_line, label });
}
