import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import ResultCard from "../ResultCard";
import type { Evidence } from "@/lib/types";

const ev: Evidence = {
  chunk_id: "abcd1234", path: "app/text.py", language: "Python", symbol: "normalize", chunking: "python-ast",
  start_line: 10, end_line: 11, content: "def normalize(t):\n    return t.strip()", similarity_score: 0.73,
  score_interpretation: "relative", signals: { lexical: 1, stack_file: true, stack_line: true, stack_function: false, symbol_mentioned: true },
};

describe("ResultCard", () => {
  it("shows path, lines, symbol, line numbers and signal badges", () => {
    render(<ResultCard ev={ev} index={2} anchorId="t-e2" onFeedback={() => {}} />);
    expect(screen.getByText("app/text.py")).toBeInTheDocument();
    expect(screen.getByText("lines 10–11")).toBeInTheDocument();
    expect(screen.getByText("normalize", { selector: "code.font-mono" })).toBeInTheDocument();
    expect(screen.getByText("11")).toBeInTheDocument();
    expect(screen.getByText("Syntax-aware")).toBeInTheDocument();
    expect(screen.getByText("stack frame hits these lines")).toBeInTheDocument();
  });
  it("reports feedback and reflects pressed state", () => {
    const fn = vi.fn();
    render(<ResultCard ev={ev} index={1} anchorId="a" feedback="useful" onFeedback={fn} />);
    expect(screen.getByLabelText("Mark snippet 1 as useful")).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByLabelText("Mark snippet 1 as irrelevant"));
    expect(fn).toHaveBeenCalledWith("irrelevant");
  });
});
