"use client";
import { useMemo, useState } from "react";
import { Download, SearchX, ShieldAlert } from "lucide-react";
import type { Evidence, FeedbackLabel, Turn } from "@/lib/types";
import { download, toJSON, toMarkdown } from "@/lib/export";
import ResultCard from "./ResultCard";
import ExplainPanel from "./ExplainPanel";

interface Props {
  turn: Turn;
  llmAvailable: boolean;
  onFeedback: (turnId: string, ev: Evidence, label: FeedbackLabel) => void;
  onExplain: (turnId: string) => void;
}

export default function TurnResults({ turn, llmAvailable, onFeedback, onExplain }: Props) {
  const data = turn.data!;
  const [langs, setLangs] = useState<Set<string>>(new Set());
  const [path, setPath] = useState("");
  const [minScore, setMinScore] = useState(0);

  const languages = useMemo(() => Array.from(new Set(data.evidence.map((e) => e.language))).sort(), [data.evidence]);
  const shown = data.evidence
    .map((ev, i) => ({ ev, index: i + 1 }))
    .filter(({ ev }) => (langs.size === 0 || langs.has(ev.language)) &&
      ev.path.toLowerCase().includes(path.toLowerCase()) && ev.similarity_score * 100 >= minScore);

  const toggle = (l: string) => setLangs((p) => { const n = new Set(p); if (n.has(l)) n.delete(l); else n.add(l); return n; });

  return (
    <div className="space-y-3">
      <p className="flex items-start gap-2 rounded-lg border border-warn/30 bg-warn/10 p-3 text-xs text-warn">
        <ShieldAlert size={15} className="mt-0.5 shrink-0" /> {data.notice}
      </p>
      {data.warnings.length > 0 && (
        <ul className="space-y-1 rounded-lg border border-line p-3 text-xs text-muted" aria-label="Warnings">
          {data.warnings.map((w) => <li key={w}>⚠ {w}</li>)}
        </ul>
      )}

      {data.evidence.length === 0 ? (
        <div className="flex items-start gap-3 rounded-lg border border-line p-4 text-sm">
          <SearchX size={18} className="mt-0.5 text-muted" />
          <p>No snippet matched your report across {data.chunks_searched} chunks in {data.files_indexed} files. Add related files, or include exact function names, file names and error text.</p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-muted">{shown.length} of {data.evidence.length} leads · {data.chunks_searched} chunks searched</span>
            <span className="ml-auto flex gap-2">
              <button onClick={() => download("codeguard-investigation.md", toMarkdown(turn), "text/markdown")}
                className="flex items-center gap-1 rounded-md border border-line px-2 py-1 hover:text-ink"><Download size={12} /> Markdown</button>
              <button onClick={() => download("codeguard-investigation.json", toJSON(turn), "application/json")}
                className="flex items-center gap-1 rounded-md border border-line px-2 py-1 hover:text-ink"><Download size={12} /> JSON</button>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs" role="group" aria-label="Filter results">
            {languages.map((l) => (
              <button key={l} onClick={() => toggle(l)} aria-pressed={langs.has(l)}
                className={`rounded-full border px-2.5 py-1 ${langs.has(l) ? "border-accent bg-accent/20" : "border-line text-muted"}`}>{l}</button>
            ))}
            <label className="sr-only" htmlFor={`path-${turn.id}`}>Filter by path</label>
            <input id={`path-${turn.id}`} value={path} onChange={(e) => setPath(e.target.value)} placeholder="Filter by path"
              className="w-36 rounded-md border border-line bg-bg px-2 py-1" />
            <label className="flex items-center gap-2 text-muted">Min score
              <input type="range" min={0} max={100} value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
            </label>
          </div>

          {shown.length === 0 ? <p className="text-sm text-muted">No results match these filters.</p> :
            shown.map(({ ev, index }) => (
              <ResultCard key={ev.chunk_id} ev={ev} index={index} anchorId={`${turn.id}-e${index}`}
                feedback={turn.feedback?.[ev.chunk_id]} onFeedback={(l) => onFeedback(turn.id, ev, l)} />
            ))}
          <ExplainPanel turnId={turn.id} state={turn.explain} llmAvailable={llmAvailable} onExplain={() => onExplain(turn.id)} />
        </>
      )}
    </div>
  );
}
