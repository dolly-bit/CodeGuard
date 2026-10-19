import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { highlightLine } from "../highlight";

const html = (line: string, lang: string) => render(<code>{highlightLine(line, lang)}</code>).container;

describe("highlightLine", () => {
  it("marks keywords, strings, numbers and comments", () => {
    const c = html("return 'a' + 42  # note", "Python");
    expect(c.querySelector(".text-accent-hover")?.textContent).toBe("return");
    expect(c.querySelector(".text-ok")?.textContent).toBe("'a'");
    expect(c.querySelector(".text-warn")?.textContent).toBe("42");
    expect(c.querySelector(".italic")?.textContent).toBe("# note");
  });
  it("uses // for C-style languages and keeps text intact", () => {
    const line = "const x = 1; // hi";
    expect(html(line, "TypeScript").textContent).toBe(line);
    expect(html("# not a comment", "TypeScript").querySelector(".italic")).toBeNull();
  });
});
