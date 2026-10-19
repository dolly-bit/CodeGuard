import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import TurnResults from "../TurnResults";
import type { Evidence, Turn } from "@/lib/types";

const sig = { lexical: 1, stack_file: false, stack_line: false, stack_function: false, symbol_mentioned: false };
const mk = (path: string, language: string, score: number, id: string): Evidence => ({
  chunk_id: id, path, language, symbol: null, chunking: "lines", start_line: 1, end_line: 1, content: "x",
  similarity_score: score, score_interpretation: "s", signals: sig });

const base = { id: "t", report: "r", fileCount: 2, topK: 5, time: "1", status: "done" as const };
const turn = (evidence: Evidence[], warnings: string[] = []): Turn => ({ ...base,
  data: { mode: "retrieval-only", notice: "Not a verified diagnosis", files_indexed: 2, chunks_searched: 2, skipped: [], warnings, evidence } });

describe("TurnResults", () => {
  it("filters by language and path", () => {
    const t = turn([mk("a.py", "Python", 0.9, "1"), mk("b.js", "JavaScript", 0.5, "2")]);
    render(<TurnResults turn={t} llmAvailable={false} onFeedback={() => {}} onExplain={() => {}} />);
    expect(screen.getByText("2 of 2 leads", { exact: false })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "JavaScript" }));
    expect(screen.getByText("1 of 2 leads", { exact: false })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "JavaScript" }));
    fireEvent.change(screen.getByLabelText("Filter by path"), { target: { value: "a.py" } });
    expect(screen.getByText("1 of 2 leads", { exact: false })).toBeInTheDocument();
  });
  it("shows an empty state, the disclaimer and warnings", () => {
    render(<TurnResults turn={turn([], ["secret redacted"])} llmAvailable={false} onFeedback={() => {}} onExplain={() => {}} />);
    expect(screen.getByText("Not a verified diagnosis")).toBeInTheDocument();
    expect(screen.getByText(/No snippet matched/)).toBeInTheDocument();
    expect(screen.getByText(/secret redacted/)).toBeInTheDocument();
  });
  it("requires consent before AI explanation", () => {
    render(<TurnResults turn={turn([mk("a.py", "Python", 0.9, "1")])} llmAvailable onFeedback={() => {}} onExplain={() => {}} />);
    const btn = screen.getByRole("button", { name: /Explain likely causes/ });
    expect(btn).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox"));
    expect(btn).toBeEnabled();
  });
});
