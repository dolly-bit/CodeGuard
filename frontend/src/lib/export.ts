import type { Turn } from "./types";

const NOTE = "Retrieval-only result: leads for investigation, not a verified diagnosis. Scores are relative, not probabilities.";

function fence(code: string): string {
  const longest = Math.max(0, ...(code.match(/`+/g) ?? []).map((s) => s.length));
  return "`".repeat(Math.max(3, longest + 1));
}

export function toMarkdown(t: Turn): string {
  const lines = [`# CodeGuard investigation`, "", `*${NOTE}*`, "", `## Bug report`, "", t.report, ""];
  if (t.data?.warnings.length) lines.push("## Warnings", "", ...t.data.warnings.map((w) => `- ${w}`), "");
  lines.push(`## Evidence (${t.data?.evidence.length ?? 0} of ${t.data?.chunks_searched ?? 0} chunks searched)`, "");
  (t.data?.evidence ?? []).forEach((e, i) => {
    const f = fence(e.content);
    lines.push(`### ${i + 1}. ${e.path}:${e.start_line}-${e.end_line}${e.symbol ? ` (${e.symbol})` : ""}`, "",
      `Language: ${e.language} · chunking: ${e.chunking} · relative score: ${e.similarity_score.toFixed(4)}`, "",
      f + e.language.toLowerCase(), e.content, f, "");
  });
  const x = t.explain?.data;
  if (x) {
    lines.push("## AI explanation (hypotheses, not verified)", "", x.summary, "");
    x.hypotheses.forEach((h) => lines.push(`- **${h.confidence}**: ${h.claim} (evidence ${h.evidence_ids.join(", ")})`));
  }
  return lines.join("\n");
}

export function toJSON(t: Turn): string {
  return JSON.stringify({ note: NOTE, report: t.report, time: t.time, result: t.data ?? null, explanation: t.explain?.data ?? null }, null, 2);
}

export function download(filename: string, text: string, mime: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
