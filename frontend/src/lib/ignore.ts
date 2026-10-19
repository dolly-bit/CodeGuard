// Mirrors backend/app/ignore.py so large folders are trimmed before upload.
const DIRS = new Set([".git", "node_modules", "vendor", "dist", "build", "__pycache__", ".next", ".venv", "venv",
  "target", "coverage", ".idea", ".vscode", ".pytest_cache", ".mypy_cache", ".gradle"]);
const LOCKS = new Set(["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "composer.lock", "gemfile.lock"]);
const BINARY = new Set(["png", "jpg", "jpeg", "gif", "webp", "ico", "pdf", "zip", "gz", "tar", "7z", "exe", "dll", "so",
  "dylib", "class", "jar", "pyc", "woff", "woff2", "ttf", "eot", "mp3", "mp4", "mov", "bin", "map"]);
const SECRET_EXT = new Set(["pem", "key", "p12", "pfx"]);
const SECRET_NAMES = new Set(["id_rsa", "id_ed25519", "id_dsa"]);

export function ignoreReason(path: string): string | null {
  const parts = path.replace(/\\/g, "/").split("/");
  const name = parts[parts.length - 1].toLowerCase();
  const ext = name.includes(".") ? name.split(".").pop()! : "";
  if (parts.includes("..")) return "unsafe path";
  if (parts.slice(0, -1).some((p) => DIRS.has(p))) return "ignored folder";
  if (LOCKS.has(name)) return "generated lock file";
  if (name.endsWith(".min.js") || name.endsWith(".min.css")) return "minified file";
  if (BINARY.has(ext)) return "binary or generated file";
  if (SECRET_NAMES.has(name) || SECRET_EXT.has(ext) || (name.startsWith(".env") && name !== ".env.example" && name !== ".env.sample"))
    return "likely secret file";
  return null;
}
