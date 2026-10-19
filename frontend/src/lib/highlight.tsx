import type { ReactNode } from "react";

const KEYWORDS = new Set(("def class return if else elif for while import from as with try except finally raise yield lambda " +
  "None True False pass break continue async await function const let var export default new this throw catch typeof null " +
  "undefined true false public private protected static final void int string bool boolean struct enum interface impl fn pub " +
  "mut use mod match func package type go chan defer select range extends implements throws namespace using override virtual self").split(" "));

const build = (marker: string) =>
  new RegExp(`(${marker}.*$)|("(?:[^"\\\\]|\\\\.)*"|'(?:[^'\\\\]|\\\\.)*')|\\b(\\d+(?:\\.\\d+)?)\\b|\\b([A-Za-z_]\\w*)\\b`, "g");
const RX = { "//": build("//"), "#": build("#"), "--": build("--") };
const HASH = new Set(["Python", "Ruby", "Shell", "YAML", "TOML", "PowerShell"]);

/** Tiny single-line highlighter: comments, strings, numbers, keywords. Not a parser. */
export function highlightLine(line: string, language: string): ReactNode[] {
  const rx = RX[language === "SQL" ? "--" : HASH.has(language) ? "#" : "//"];
  rx.lastIndex = 0;
  const out: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = rx.exec(line))) {
    if (m.index > last) out.push(line.slice(last, m.index));
    const [txt, comment, str, num, word] = m;
    const key = out.length;
    if (comment) out.push(<span key={key} className="italic text-muted">{txt}</span>);
    else if (str) out.push(<span key={key} className="text-ok">{txt}</span>);
    else if (num) out.push(<span key={key} className="text-warn">{txt}</span>);
    else if (word && KEYWORDS.has(word)) out.push(<span key={key} className="text-accent-hover">{txt}</span>);
    else out.push(txt);
    last = m.index + txt.length;
    if (txt.length === 0) rx.lastIndex++;
  }
  if (last < line.length) out.push(line.slice(last));
  return out;
}
