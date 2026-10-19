"use client";
import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import type { ExplainState } from "@/lib/types";

interface Props {
  turnId: string;
  state?: ExplainState;
  llmAvailable: boolean;
  onExplain: () => void;
}

export default function ExplainPanel({ turnId, state, llmAvailable, onExplain }: Props) {
  const [consent, setConsent] = useState(false);
  const data = state?.data;

  return (
    <section aria-label="AI explanation" className="rounded-xl border border-line p-4 text-sm">
      <h3 className="flex items-center gap-2 font-medium"><Sparkles size={16} className="text-accent-hover" /> Explain with AI (optional)</h3>

      {!llmAvailable ? (
        <p className="mt-2 text-muted">Not configured on this server. Set <code className="font-mono text-pink">ANTHROPIC_API_KEY</code> on the backend to enable it.</p>
      ) : !data ? (
        <>
          <label className="mt-3 flex items-start gap-2 text-xs text-muted">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
            I understand the bug report and the snippets above will be sent to an external AI provider.
          </label>
          <button disabled={!consent || state?.status === "loading"} onClick={onExplain}
            className="mt-3 flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-white hover:bg-accent-hover disabled:opacity-50">
            {state?.status === "loading" && <Loader2 size={14} className="animate-spin" />} Explain likely causes
          </button>
        </>
      ) : (
        <div className="mt-3 space-y-3">
          <p className="rounded-lg border border-warn/30 bg-warn/10 p-2 text-xs text-warn">
            Hypotheses generated from the retrieved snippets. Not verified: reproduce and test before trusting.
          </p>
          <p>{data.summary}</p>
          {data.hypotheses.map((h, i) => (
            <div key={i} className="rounded-lg border border-line bg-panel p-3">
              <p><span className="mr-2 rounded bg-line px-1.5 py-0.5 text-xs">{h.confidence} confidence</span>{h.claim}</p>
              <p className="mt-2 text-xs text-muted">
                Evidence:{" "}
                {h.evidence_ids.map((n) => (
                  <a key={n} href={`#${turnId}-e${n}`} className="mr-2 text-accent-hover underline">snippet {n}</a>
                ))}
              </p>
              {h.counter_evidence && <p className="mt-1 text-xs text-muted">Against: {h.counter_evidence}</p>}
            </div>
          ))}
          {data.next_steps.length > 0 && (
            <ul className="list-disc space-y-1 pl-5 text-muted">{data.next_steps.map((n, i) => <li key={i}>{n}</li>)}</ul>
          )}
          <p className="text-xs text-muted">Model: {data.model}</p>
        </div>
      )}
      {state?.status === "error" && <p role="alert" className="mt-3 text-bad">{state.error}</p>}
    </section>
  );
}
