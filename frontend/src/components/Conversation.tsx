import { Eye, Loader2 } from "lucide-react";
import type { Evidence, FeedbackLabel, Turn } from "@/lib/types";
import TurnResults from "./TurnResults";

interface Props {
  turns: Turn[];
  llmAvailable: boolean;
  onFeedback: (turnId: string, ev: Evidence, label: FeedbackLabel) => void;
  onExplain: (turnId: string) => void;
}

export default function Conversation({ turns, llmAvailable, onFeedback, onExplain }: Props) {
  if (turns.length === 0) {
    return (
      <div className="m-auto max-w-md text-center text-sm text-muted">
        <p className="mb-2 text-base text-ink">Describe the bug, then add the files to search.</p>
        <p>Paste the stack trace if you have one: file names, line numbers and function names are used to rank results. Exact identifiers like <code className="font-mono text-pink">normalize</code> help too.</p>
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {turns.map((t) => (
        <div key={t.id} className="space-y-4">
          <div className="ml-auto max-w-[85%] rounded-xl border border-accent/40 bg-accent/10 p-4 lg:max-w-[70%]">
            <div className="mb-2 flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-line text-sm">D</span>
              <span className="text-sm font-medium">You</span>
            </div>
            <p className="whitespace-pre-wrap text-sm">{t.report}</p>
            <p className="mt-3 flex items-center gap-1.5 text-xs text-muted"><Eye size={13} /> {t.fileCount} file{t.fileCount === 1 ? "" : "s"} · top {t.topK}</p>
          </div>

          <div className="max-w-full rounded-xl border border-line bg-panel p-4 lg:max-w-[88%]">
            <div className="mb-3 flex items-center gap-3 text-sm">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-ink text-xs font-semibold text-bg">CG</span>
              <span className="font-medium">CodeGuard</span>
              <span className="ml-auto text-xs text-muted">{t.time}</span>
            </div>
            {t.status === "loading" && (
              <p role="status" className="flex items-center gap-2 text-sm text-muted"><Loader2 className="animate-spin" size={16} /> Searching your files…</p>
            )}
            {t.status === "error" && (
              <div role="alert" className="rounded-lg border border-bad/40 bg-bad/10 p-3 text-sm">
                <p className="font-medium text-bad">The search did not complete</p>
                <p className="mt-1 text-ink/80">{t.error}</p>
              </div>
            )}
            {t.status === "done" && t.data && (
              <TurnResults turn={t} llmAvailable={llmAvailable} onFeedback={onFeedback} onExplain={onExplain} />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
