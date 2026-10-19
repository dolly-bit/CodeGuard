"use client";
import { useEffect, useRef, useState } from "react";
import { Gauge, Maximize2, Menu, Trash2 } from "lucide-react";
import { LIMITS } from "@/lib/limits";

interface Props {
  online: boolean | null;
  topK: number;
  setTopK: (n: number) => void;
  onMenu: () => void;
  usage: { files: number; bytes: number; requests: number };
  persist: boolean;
  setPersist: (v: boolean) => void;
  onClearHistory: () => void;
}

export default function TopBar({ online, topK, setTopK, onMenu, usage, persist, setPersist, onClearHistory }: Props) {
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const outside = (e: MouseEvent) => { if (!wrap.current?.contains(e.target as Node)) setOpen(false); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") { setOpen(false); trigger.current?.focus(); } };
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("mousedown", outside); document.removeEventListener("keydown", esc); };
  }, [open]);

  const pct = Math.min(100, (usage.bytes / LIMITS.totalBytes) * 100);
  const dot = online === null ? "bg-muted" : online ? "bg-ok" : "bg-bad";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-line px-4">
      <button onClick={onMenu} className="rounded-lg p-2 hover:bg-panel-2 lg:hidden" aria-label="Open menu"><Menu size={20} /></button>
      <h1 className="flex-1 text-center text-base font-medium lg:text-left">Debugging with evidence</h1>

      <div className="flex items-center gap-2">
        <span className="hidden items-center gap-2 rounded-lg border border-line px-3 py-2 text-xs sm:flex" role="status">
          <span className={`h-2 w-2 rounded-full ${dot}`} />
          {online === null ? "Checking API" : online ? "API online" : "API offline"}
        </span>

        <div className="relative" ref={wrap}>
          <button ref={trigger} onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-haspopup="dialog"
            className="flex items-center gap-2 rounded-lg bg-panel-2 px-3 py-2 text-sm hover:bg-line">
            <Gauge size={16} /> Limits
          </button>
          {open && (
            <div role="dialog" aria-label="Session limits and privacy" className="absolute right-0 top-12 z-50 w-80 rounded-xl border border-line bg-panel p-4 shadow-2xl">
              <Row k="Mode" v="Retrieval + optional AI" />
              <Row k="Engine" v="BM25 + stack-trace boosts" />
              <Row k="Requests this session" v={String(usage.requests)} />
              <Row k="Files selected" v={`${usage.files} / ${LIMITS.files}`} />
              <div className="mt-3 flex justify-between text-sm"><span>Source size</span>
                <span>{(usage.bytes / 1000).toFixed(0)}k / {(LIMITS.totalBytes / 1000).toLocaleString("en-US")}k</span></div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-line" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100} aria-label="Source size used">
                <div className="h-full rounded-full bg-ok" style={{ width: `${pct}%` }} />
              </div>
              <hr className="my-4 border-line" />
              <label className="flex items-center justify-between text-sm">
                Results (top_k)
                <input type="number" min={LIMITS.topK.min} max={LIMITS.topK.max} value={topK}
                  onChange={(e) => setTopK(Math.max(LIMITS.topK.min, Math.min(LIMITS.topK.max, Number(e.target.value) || 1)))}
                  className="w-16 rounded-md border border-line bg-bg px-2 py-1 text-right" />
              </label>
              <label className="mt-3 flex items-start gap-2 text-xs text-muted">
                <input type="checkbox" checked={persist} onChange={(e) => setPersist(e.target.checked)} className="mt-0.5" />
                Save history on this device (stores snippets in your browser only)
              </label>
              <button onClick={onClearHistory} className="mt-3 flex items-center gap-2 text-xs text-muted hover:text-bad"><Trash2 size={12} /> Delete history</button>
            </div>
          )}
        </div>

        <button className="hidden rounded-lg p-2 text-accent-hover hover:bg-panel-2 sm:block" aria-label="Toggle fullscreen"
          onClick={() => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen())}>
          <Maximize2 size={18} />
        </button>
        <div className="grid h-9 w-9 place-items-center rounded-full bg-line text-sm" aria-hidden>D</div>
      </div>
    </header>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return <div className="mb-2 flex justify-between text-sm"><span className="text-muted">{k}</span><span>{v}</span></div>;
}
