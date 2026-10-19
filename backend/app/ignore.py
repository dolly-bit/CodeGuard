"""Server-side ignore rules (mirrors frontend/src/lib/ignore.ts)."""
from typing import Iterable, List, Optional, Tuple

IGNORED_DIRS = {".git", "node_modules", "vendor", "dist", "build", "__pycache__", ".next", ".venv", "venv",
                "target", "coverage", ".idea", ".vscode", ".pytest_cache", ".mypy_cache", ".gradle"}
LOCK_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock",
              "composer.lock", "gemfile.lock"}
BINARY_EXT = {"png", "jpg", "jpeg", "gif", "webp", "ico", "pdf", "zip", "gz", "tar", "7z", "exe", "dll", "so",
              "dylib", "class", "jar", "pyc", "woff", "woff2", "ttf", "eot", "mp3", "mp4", "mov", "bin", "map"}
SECRET_EXT = {"pem", "key", "p12", "pfx"}
SECRET_NAMES = {"id_rsa", "id_ed25519", "id_dsa"}


def ignore_reason(path: str, content: Optional[str] = None) -> Optional[str]:
    parts = path.replace("\\", "/").split("/")
    name = parts[-1].lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ".." in parts:
        return "unsafe path"
    if any(p in IGNORED_DIRS for p in parts[:-1]):
        return "ignored folder"
    if name in LOCK_FILES:
        return "generated lock file"
    if name.endswith((".min.js", ".min.css")):
        return "minified file"
    if ext in BINARY_EXT:
        return "binary or generated file"
    if name in SECRET_NAMES or ext in SECRET_EXT or (
            name.startswith(".env") and name not in (".env.example", ".env.sample")):
        return "likely secret file"
    if content is not None and "\x00" in content:
        return "binary content"
    return None


def filter_files(files: Iterable[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    kept, skipped = [], []
    for path, content in files:
        reason = ignore_reason(path, content)
        (skipped.append((path, reason)) if reason else kept.append((path, content)))
    return kept, skipped
