import { afterEach, describe, expect, it, vi } from "vitest";
import { analyze } from "../api";

const ok = {
  mode: "retrieval-only", notice: "n", files_indexed: 1, chunks_searched: 1, skipped: [], warnings: [],
  evidence: [{ chunk_id: "abcd", path: "a.py", language: "Python", symbol: null, chunking: "lines", start_line: 1, end_line: 1,
    content: "x", similarity_score: 0.5, score_interpretation: "s",
    signals: { lexical: 1, stack_file: false, stack_line: false, stack_function: false, symbol_mentioned: false } }],
};

afterEach(() => vi.unstubAllGlobals());

describe("analyze", () => {
  it("returns validated data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(ok), { status: 200 })));
    expect((await analyze("bug", [{ path: "a.py", content: "x" }], 3)).evidence).toHaveLength(1);
  });
  it("explains network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fail")));
    await expect(analyze("b", [], 1)).rejects.toThrow(/Cannot reach the backend/);
  });
  it("surfaces validation detail and request id", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: [{ msg: "bad report" }] }),
      { status: 422, headers: { "X-Request-ID": "rid123" } })));
    await expect(analyze("b", [], 1)).rejects.toThrow("bad report (ref rid123)");
  });
  it("mentions retry time on 429", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Rate limit" }),
      { status: 429, headers: { "Retry-After": "12" } })));
    await expect(analyze("b", [], 1)).rejects.toThrow(/12 seconds/);
  });
  it("rejects malformed responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ hello: 1 }), { status: 200 })));
    await expect(analyze("b", [], 1)).rejects.toThrow(/unexpected response/);
  });
});
