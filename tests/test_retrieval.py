
from app.retrieval import retrieve_evidence, chunk_source


def test_retrieves_relevant_file_first():
    bug_report = (
        "The text normalization function crashes because "
        "text.strip() fails."
    )
    files = [
        {
            "path": "app/routes/users.py",
            "content": "def get_email(user):\n    return user.email\n",
        },
        {
            "path": "app/services/orders.py",
            "content": (
                "def total_price(items):\n"
                "    return sum(item.price for item in items)\n"
            ),
        },
        {
            "path": "app/utils/text.py",
            "content": (
                "def normalize(text):\n"
                "    return text.strip().lower()\n"
            ),
        },
    ]

    evidence = retrieve_evidence(bug_report, files, top_k=3)

    assert evidence
    assert evidence[0]["path"] == "app/utils/text.py"
    assert "text.strip()" in evidence[0]["content"]


def test_chunk_source_preserves_line_numbers():
    content = "line one\nline two\nline three"

    chunks = chunk_source("example.py", content, chunk_lines=2, overlap=1)

    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 2
    assert chunks[1]["start_line"] == 2
    assert chunks[1]["end_line"] == 3


def test_empty_files_return_no_evidence():
    assert retrieve_evidence("Why does this crash?", []) == []
