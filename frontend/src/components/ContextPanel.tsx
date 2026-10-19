import { FileCode2, FolderOpen, Plus, X } from "lucide-react";
import type { SourceFile } from "@/lib/types";
import { languageOf } from "@/lib/lang";
import { LIMITS } from "@/lib/limits";

interface Props {
  files: SourceFile[];
  skippedSummary: string;
  onAddFiles: () => void;
  onAddFolder: () => void;
  onRemove: (path: string) => void;
  onClear: () => void;
}

export default function ContextPanel({ files, skippedSummary, onAddFiles, onAddFolder, onRemove, onClear }: Props) {
  const langs = files.reduce<Record<string, number>>((m, f) => ({ ...m, [languageOf(f.path)]: (m[languageOf(f.path)] ?? 0) + 1 }), {});
  return (
    <aside className="hidden w-80 shrink-0 flex-col gap-4 border-l border-line p-5 xl:flex" aria-label="Context files">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Context</h2>
        {files.length > 0 && <button onClick={onClear} className="text-xs text-muted hover:text-bad">Clear all</button>}
      </div>

      {files.length === 0 ? (
        <div className="rounded-xl border border-line bg-panel p-4 text-sm text-muted">No context added yet</div>
      ) : (
        <>
          <p className="text-xs text-muted">
            {files.length} / {LIMITS.files} files · {Object.entries(langs).map(([l, n]) => `${l} ${n}`).join(", ")}
          </p>
          <ul className="space-y-2 overflow-y-auto">
            {files.map((f) => (
              <li key={f.path} className="flex items-center gap-3 rounded-lg border border-line bg-panel p-3">
                <FileCode2 size={18} className="shrink-0 text-accent-hover" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm" title={f.path}>{f.path}</p>
                  <p className="text-xs text-muted">{languageOf(f.path)} · {(f.content.length / 1000).toFixed(1)} KB</p>
                </div>
                <button onClick={() => onRemove(f.path)} aria-label={`Remove ${f.path}`} className="rounded p-1 text-muted hover:text-bad"><X size={16} /></button>
              </li>
            ))}
          </ul>
        </>
      )}
      {skippedSummary && <p className="rounded-lg border border-line p-3 text-xs text-muted">Skipped: {skippedSummary}</p>}

      <div className="mt-auto grid gap-2">
        <button onClick={onAddFiles} className="flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-white hover:bg-accent-hover"><Plus size={16} /> Add files or .zip</button>
        <button onClick={onAddFolder} className="flex items-center justify-center gap-2 rounded-lg border border-accent px-4 py-2.5 text-accent-hover hover:bg-accent/10"><FolderOpen size={16} /> Add folder</button>
      </div>
    </aside>
  );
}
