import { FileCode2, ThumbsDown, ThumbsUp } from "lucide-react";
import type { Evidence, FeedbackLabel } from "@/lib/types";
import { highlightLine } from "@/lib/highlight";

const CHUNKING: Record<string, string> = {
  "python-ast": "Syntax-aware",
  "heuristic-brace": "Heuristic split",
  lines: "Line window",
};

interface Props {
  ev: Evidence;
  index: number; // 1-based position in the full result list (used by AI citations)
  anchorId: string;
  feedback?: FeedbackLabel;
  onFeedback: (label: FeedbackLabel) => void;
}

export default function ResultCard({ ev, index, anchorId, feedback, onFeedback }: Props) {
  const s = ev.signals;
  const badges = [
    s.stack_line && "stack frame hits these lines",
    !s.stack_line && s.stack_file && "file named in trace",
    s.stack_function && "function named in trace",
    s.symbol_mentioned && "named in report",
  ].filter(Boolean) as string[];

  return (
    <article id={anchorId} className="scroll-mt-4 overflow-hidden rounded-xl border border-line bg-bg">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line px-4 py-2.5 text-sm">
        <span className="text-muted">#{index}</span>
        <FileCode2 size={15} className="text-pink" />
        <span className="font-medium text-pink">{ev.path}</span>
        <span className="text-muted">lines {ev.start_line}–{ev.end_line}</span>
        {ev.symbol && <code className="rounded bg-line px-1.5 py-0.5 font-mono text-xs">{ev.symbol}</code>}
        <span className="rounded bg-line px-1.5 py-0.5 text-xs text-muted">{ev.language}</span>
        <span className="ml-auto flex items-center gap-2" title={ev.score_interpretation}>
          <span className="h-1.5 w-20 overflow-hidden rounded-full bg-line">
            <span className="block h-full bg-accent" style={{ width: `${Math.max(4, ev.similarity_score * 100)}%` }} />
          </span>
          <span className="font-mono text-xs">{ev.similarity_score.toFixed(4)}</span>
        </span>
      </header>

      <div className="flex flex-wrap gap-1.5 border-b border-line px-4 py-2 text-xs">
        <span className="rounded-full border border-line px-2 py-0.5 text-muted">{CHUNKING[ev.chunking] ?? ev.chunking}</span>
        {badges.map((b) => <span key={b} className="rounded-full border border-accent/50 px-2 py-0.5 text-accent-hover">{b}</span>)}
      </div>

      <pre className="max-h-72 overflow-auto px-4 py-3 font-mono text-[13px] leading-6">
        {ev.content.split("\n").map((l, i) => (
          <div key={i} className="flex">
            <span className="mr-4 w-8 shrink-0 select-none text-right text-muted">{ev.start_line + i}</span>
            <code className="whitespace-pre">{l ? highlightLine(l, ev.language) : " "}</code>
          </div>
        ))}
      </pre>

      <footer className="flex items-center gap-2 border-t border-line px-4 py-2 text-xs text-muted">
        <span>Was this useful?</span>
        {(["useful", "irrelevant"] as const).map((label) => (
          <button key={label} onClick={() => onFeedback(label)} aria-pressed={feedback === label}
            aria-label={`Mark snippet ${index} as ${label}`}
            className={`flex items-center gap-1 rounded-md border px-2 py-1 ${feedback === label ? "border-accent bg-accent/20 text-ink" : "border-line hover:text-ink"}`}>
            {label === "useful" ? <ThumbsUp size={12} /> : <ThumbsDown size={12} />} {label === "useful" ? "Useful" : "Irrelevant"}
          </button>
        ))}
      </footer>
    </article>
  );
}
