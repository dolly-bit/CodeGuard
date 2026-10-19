import { describe, expect, it } from "vitest";
import { toJSON, toMarkdown } from "../export";
import type { Turn } from "../types";

const turn: Turn = {
  id: "t", report: "it crashes", fileCount: 1, topK: 3, time: "10:00", status: "done",
  data: { mode: "retrieval-only", notice: "n", files_indexed: 1, chunks_searched: 2, skipped: [], warnings: ["w1"],
    evidence: [{ chunk_id: "abcd", path: "a.md", language: "Markdown", symbol: "f", chunking: "lines", start_line: 3, end_line: 5,
      content: "```js\ncode\n```", similarity_score: 0.5, score_interpretation: "s",
      signals: { lexical: 1, stack_file: false, stack_line: false, stack_function: false, symbol_mentioned: false } }] },
};

describe("export", () => {
  it("markdown keeps the disclaimer, warnings and uses a longer fence around backticks", () => {
    const md = toMarkdown(turn);
    expect(md).toContain("not a verified diagnosis");
    expect(md).toContain("- w1");
    expect(md).toContain("a.md:3-5 (f)");
    expect(md).toContain("````markdown");
  });
  it("json round-trips", () => {
    expect(JSON.parse(toJSON(turn)).report).toBe("it crashes");
  });
});
