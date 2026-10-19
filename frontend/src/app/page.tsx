"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { FolderOpen, Paperclip, SendHorizontal, X } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import ContextPanel from "@/components/ContextPanel";
import Conversation from "@/components/Conversation";
import { analyze, checkHealth, explain, sendFeedback } from "@/lib/api";
import { ingest, summarizeSkipped } from "@/lib/files";
import { ACCEPT } from "@/lib/lang";
import { LIMITS } from "@/lib/limits";
import type { Evidence, FeedbackLabel, SourceFile, Turn } from "@/lib/types";

const HISTORY_KEY = "codeguard.history.v1";
const PERSIST_KEY = "codeguard.persist";

export default function Home() {
  const [menu, setMenu] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);
  const [llm, setLlm] = useState(false);
  const [files, setFiles] = useState<SourceFile[]>([]);
  const [report, setReport] = useState("");
  const [topK, setTopK] = useState(5);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [notice, setNotice] = useState("");
  const [skipped, setSkipped] = useState("");
  const [busy, setBusy] = useState(false);
  const [requests, setRequests] = useState(0);
  const [persist, setPersistState] = useState(false);
  const picker = useRef<HTMLInputElement>(null);
  const folder = useRef<HTMLInputElement>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => { checkHealth().then((h) => { setOnline(h.online); setLlm(h.llm); }); }, []);
  useEffect(() => { folder.current?.setAttribute("webkitdirectory", ""); }, []);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [turns.length]);

  // Opt-in history, stored only in this browser. Reading storage must happen after mount (SSR-safe).
  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect */
    try {
      if (localStorage.getItem(PERSIST_KEY) === "1") {
        setPersistState(true);
        const raw = localStorage.getItem(HISTORY_KEY);
        if (raw) setTurns(JSON.parse(raw) as Turn[]);
      }
    } catch { /* storage unavailable */ }
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);
  useEffect(() => {
    if (!persist) return;
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(turns.filter((t) => t.status !== "loading"))); } catch { /* quota */ }
  }, [turns, persist]);

  const setPersist = (v: boolean) => {
    setPersistState(v);
    try {
      if (v) localStorage.setItem(PERSIST_KEY, "1");
      else { localStorage.removeItem(PERSIST_KEY); localStorage.removeItem(HISTORY_KEY); }
    } catch { /* ignore */ }
  };
  const clearHistory = () => {
    setTurns([]);
    try { localStorage.removeItem(HISTORY_KEY); } catch { /* ignore */ }
  };

  const bytes = files.reduce((n, f) => n + new TextEncoder().encode(f.content).length, 0);

  const onPick = useCallback(async (list: FileList | null) => {
    if (!list || list.length === 0) return;
    setNotice("Reading files…");
    const res = await ingest(Array.from(list), LIMITS.totalBytes - bytes, files.length);
    setFiles((prev) => {
      const map = new Map(prev.map((p) => [p.path, p]));
      res.files.forEach((f) => map.set(f.path, f));
      return Array.from(map.values());
    });
    setSkipped(summarizeSkipped(res.skipped));
    setNotice(res.files.length === 0 ? "No usable source files were found in that selection." : "");
    if (picker.current) picker.current.value = "";
    if (folder.current) folder.current.value = "";
  }, [bytes, files.length]);

  const patch = (id: string, p: Partial<Turn>) => setTurns((t) => t.map((x) => (x.id === id ? { ...x, ...p } : x)));
  const remove = (path: string) => setFiles((p) => p.filter((f) => f.path !== path));

  const submit = async () => {
    if (busy) return;
    if (!report.trim()) { setNotice("Write a bug report before searching."); return; }
    if (files.length === 0) { setNotice("Add at least one source file."); return; }
    setNotice("");
    const id = crypto.randomUUID();
    const turn: Turn = { id, report: report.trim(), fileCount: files.length, topK, status: "loading",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) };
    setTurns((t) => [...t, turn]);
    setReport("");
    setBusy(true);
    setRequests((n) => n + 1);
    try {
      patch(id, { status: "done", data: await analyze(turn.report, files, topK) });
      setOnline(true);
    } catch (e) {
      patch(id, { status: "error", error: (e as Error).message });
    } finally {
      setBusy(false);
    }
  };

  const onFeedback = async (turnId: string, ev: Evidence, label: FeedbackLabel) => {
    setTurns((ts) => ts.map((t) => (t.id === turnId ? { ...t, feedback: { ...t.feedback, [ev.chunk_id]: label } } : t)));
    try { await sendFeedback(ev, label); } catch { setNotice("Could not save feedback. Is the backend running?"); }
  };

  const onExplain = async (turnId: string) => {
    const t = turns.find((x) => x.id === turnId);
    if (!t?.data) return;
    patch(turnId, { explain: { status: "loading" } });
    try {
      const data = await explain(t.report, t.data.evidence.slice(0, LIMITS.llmEvidence), true);
      patch(turnId, { explain: { status: "done", data } });
    } catch (e) {
      patch(turnId, { explain: { status: "error", error: (e as Error).message } });
    }
  };

  return (
    <div className="flex h-dvh overflow-hidden">
      <a href="#report" className="sr-only z-50 rounded bg-accent px-3 py-2 text-white focus:not-sr-only focus:absolute focus:left-2 focus:top-2">Skip to bug report</a>
      <Sidebar open={menu} onClose={() => setMenu(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar online={online} topK={topK} setTopK={setTopK} onMenu={() => setMenu(true)}
          usage={{ files: files.length, bytes, requests }} persist={persist} setPersist={setPersist} onClearHistory={clearHistory} />
        <div className="flex min-h-0 flex-1">
          <main className="flex min-w-0 flex-1 flex-col">
            <div className="flex flex-1 flex-col overflow-y-auto p-4 lg:p-6">
              <Conversation turns={turns} llmAvailable={llm} onFeedback={onFeedback} onExplain={onExplain} />
              <div ref={bottom} />
            </div>

            <div className="border-t border-line p-4">
              {files.length > 0 && (
                <ul className="mb-3 flex max-h-24 flex-wrap gap-2 overflow-y-auto xl:hidden">
                  {files.map((f) => (
                    <li key={f.path} className="flex items-center gap-1.5 rounded-full border border-line bg-panel px-3 py-1 text-xs">
                      {f.path}
                      <button onClick={() => remove(f.path)} aria-label={`Remove ${f.path}`}><X size={12} /></button>
                    </li>
                  ))}
                </ul>
              )}
              {notice && <p role="alert" className="mb-2 text-sm text-warn">{notice}</p>}
              <div className="flex items-end gap-2 rounded-xl border border-line bg-panel px-4 py-3 focus-within:border-accent">
                <label htmlFor="report" className="sr-only">Bug report</label>
                <textarea id="report" rows={2} value={report} maxLength={LIMITS.reportChars} onChange={(e) => setReport(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(); }}
                  placeholder="Describe the bug and paste any stack trace… (Ctrl+Enter to send)"
                  className="max-h-40 min-h-10 flex-1 resize-none bg-transparent text-sm outline-none placeholder:text-muted" />
                <input ref={picker} type="file" multiple accept={ACCEPT} className="hidden" onChange={(e) => onPick(e.target.files)} />
                <input ref={folder} type="file" multiple className="hidden" onChange={(e) => onPick(e.target.files)} />
                <button onClick={() => picker.current?.click()} aria-label="Attach files or zip" className="rounded-lg p-2 text-muted hover:text-ink xl:hidden"><Paperclip size={18} /></button>
                <button onClick={() => folder.current?.click()} aria-label="Attach folder" className="rounded-lg p-2 text-muted hover:text-ink xl:hidden"><FolderOpen size={18} /></button>
                <button onClick={submit} disabled={busy} aria-label="Search for evidence"
                  className="rounded-lg bg-accent p-2.5 text-white hover:bg-accent-hover disabled:opacity-50"><SendHorizontal size={18} /></button>
              </div>
              <p className="mt-2 text-xs text-muted">
                Files are read in your browser and sent only to your own API. Likely secrets are redacted server-side.
              </p>
            </div>
          </main>
          <ContextPanel files={files} skippedSummary={skipped} onAddFiles={() => picker.current?.click()}
            onAddFolder={() => folder.current?.click()} onRemove={remove} onClear={() => { setFiles([]); setSkipped(""); }} />
        </div>
      </div>
    </div>
  );
}
