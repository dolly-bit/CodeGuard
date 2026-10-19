EXT = {
    "py": "Python", "pyw": "Python",
    "js": "JavaScript", "jsx": "JavaScript", "mjs": "JavaScript", "cjs": "JavaScript",
    "ts": "TypeScript", "tsx": "TypeScript", "java": "Java",
    "c": "C", "h": "C", "cc": "C++", "cpp": "C++", "hpp": "C++", "cs": "C#", "go": "Go", "rs": "Rust",
    "php": "PHP", "rb": "Ruby", "kt": "Kotlin", "kts": "Kotlin", "swift": "Swift", "sql": "SQL",
    "html": "HTML", "css": "CSS", "scss": "SCSS", "json": "JSON", "yaml": "YAML", "yml": "YAML",
    "toml": "TOML", "xml": "XML", "sh": "Shell", "bash": "Shell", "ps1": "PowerShell",
    "md": "Markdown", "txt": "Text",
}
# Languages handled by the heuristic declaration splitter (not a real parser).
BRACE_LANGUAGES = {"JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go", "Rust", "PHP", "Kotlin", "Swift"}


def detect_language(path: str) -> str:
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    if name in ("Dockerfile", "Makefile"):
        return name
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return EXT.get(ext, "Text")
