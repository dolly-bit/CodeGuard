import { describe, expect, it } from "vitest";
import { ignoreReason } from "../ignore";

describe("ignoreReason", () => {
  it("skips dependency, build and binary paths", () => {
    expect(ignoreReason("node_modules/x/index.js")).toBe("ignored folder");
    expect(ignoreReason("web/dist/app.js")).toBe("ignored folder");
    expect(ignoreReason("img/logo.png")).toBe("binary or generated file");
    expect(ignoreReason("yarn.lock")).toBe("generated lock file");
  });
  it("skips likely secrets but keeps .env.example", () => {
    expect(ignoreReason(".env")).toBe("likely secret file");
    expect(ignoreReason("certs/server.pem")).toBe("likely secret file");
    expect(ignoreReason(".env.example")).toBeNull();
  });
  it("rejects traversal and accepts normal source", () => {
    expect(ignoreReason("../etc/passwd")).toBe("unsafe path");
    expect(ignoreReason("src\\app\\main.py")).toBeNull();
  });
});
