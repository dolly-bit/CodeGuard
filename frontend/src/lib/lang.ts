// L0 labels only: extension-based. Not evidence of syntax-aware support.
const MAP: Record<string, string> = {
  py: "Python", js: "JavaScript", jsx: "JavaScript", mjs: "JavaScript", cjs: "JavaScript",
  ts: "TypeScript", tsx: "TypeScript", java: "Java", c: "C", h: "C", cc: "C++", cpp: "C++", hpp: "C++",
  cs: "C#", go: "Go", rs: "Rust", php: "PHP", rb: "Ruby", kt: "Kotlin", kts: "Kotlin", swift: "Swift",
  sql: "SQL", html: "HTML", css: "CSS", scss: "SCSS", json: "JSON", yaml: "YAML", yml: "YAML",
  toml: "TOML", xml: "XML", sh: "Shell", bash: "Shell", ps1: "PowerShell", md: "Markdown", txt: "Text",
};

export const ACCEPT = [...Object.keys(MAP).map((e) => `.${e}`), ".zip"].join(",");

export function languageOf(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return MAP[ext] ?? "Text";
}
