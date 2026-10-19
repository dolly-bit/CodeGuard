from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def chunk_source(path: str, content: str, chunk_lines: int = 40, overlap: int = 8):
    # Split source into line-numbered overlapping chunks.
    lines = content.splitlines()
    if not lines:
        return []

    chunks = []
    start = 0
    while start < len(lines):
        end = min(start + chunk_lines, len(lines))
        chunks.append({
            "path": path,
            "start_line": start + 1,
            "end_line": end,
            "content": "\n".join(lines[start:end]),
        })
        if end == len(lines):
            break
        start = end - overlap
    return chunks


def retrieve_evidence(bug_report: str, files: list[dict], top_k: int = 5):
    chunks = []
    for file in files:
        chunks.extend(chunk_source(file["path"], file["content"]))

    if not chunks:
        return []

    documents = [bug_report] + [chunk["content"] for chunk in chunks]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        token_pattern=r"(?u)\b[\w.]+\b",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return []

    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    ranked = sorted(
        zip(chunks, scores),
        key=lambda pair: (-float(pair[1]), pair[0]["path"], pair[0]["start_line"]),
    )[:top_k]

    return [
        {
            **chunk,
            "similarity_score": round(float(score), 4),
            "score_interpretation": "relative retrieval similarity; not a probability",
        }
        for chunk, score in ranked
    ]
