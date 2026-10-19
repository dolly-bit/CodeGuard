import { strFromU8, unzipSync } from "fflate";
import { ignoreReason } from "./ignore";
import { LIMITS } from "./limits";
import type { SkippedFile, SourceFile } from "./types";

export interface IngestResult { files: SourceFile[]; skipped: SkippedFile[] }

export function summarizeSkipped(skipped: SkippedFile[]): string {
  const by = new Map<string, number>();
  skipped.forEach((s) => by.set(s.reason, (by.get(s.reason) ?? 0) + 1));
  return Array.from(by, ([r, n]) => `${n} × ${r}`).join(", ");
}

/** Read files, folders (webkitRelativePath) and .zip archives. `budget` = bytes still available. */
export async function ingest(list: File[], budget: number, existing = 0): Promise<IngestResult> {
  const files: SourceFile[] = [];
  const skipped: SkippedFile[] = [];
  let used = 0;
  let count = existing;

  const add = (path: string, text: string) => {
    const bytes = new TextEncoder().encode(text).length;
    if (text.includes("\u0000")) return skipped.push({ path, reason: "binary content" });
    if (count >= LIMITS.files) return skipped.push({ path, reason: `over ${LIMITS.files}-file limit` });
    if (used + bytes > budget) return skipped.push({ path, reason: "total size limit reached" });
    used += bytes;
    count += 1;
    files.push({ path, content: text });
  };

  for (const f of list) {
    const path = f.webkitRelativePath || f.name;
    if (f.name.toLowerCase().endsWith(".zip")) {
      if (f.size > LIMITS.zipBytes) { skipped.push({ path, reason: "zip over 20 MB" }); continue; }
      try {
        let entries = 0;
        const out = unzipSync(new Uint8Array(await f.arrayBuffer()), {
          filter: (e) => {
            if (e.name.endsWith("/")) return false;
            if (++entries > LIMITS.zipEntries) return false;
            const why = ignoreReason(e.name) ?? (e.originalSize > LIMITS.fileBytes ? "file over 500 KB" : null);
            if (why) { skipped.push({ path: e.name, reason: why }); return false; }
            return true;
          },
        });
        for (const [name, bytes] of Object.entries(out)) add(name, strFromU8(bytes));
      } catch {
        skipped.push({ path, reason: "unreadable zip" });
      }
      continue;
    }
    const why = ignoreReason(path) ?? (f.size > LIMITS.fileBytes ? "file over 500 KB" : null);
    if (why) { skipped.push({ path, reason: why }); continue; }
    add(path, await f.text());
  }
  return { files, skipped };
}
