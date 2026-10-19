from app.chunking import chunk_file, _windows


def test_line_windows_and_overlap():
    text = "\n".join(f"line{i}" for i in range(1, 101))
    c = chunk_file("notes.txt", text)
    assert (c[0].start_line, c[0].end_line) == (1, 40)
    assert c[1].start_line == 33 and c[-1].end_line == 100
    assert all(x.chunking == "lines" for x in c)


def test_bad_window_params():
    try:
        _windows("a", ["x"], 1, "Text", None, "lines", size=5, overlap=5)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_empty_file_gives_no_chunks():
    assert chunk_file("a.py", "  \n\n") == []


def test_python_ast_symbols_and_decorators():
    src = "import os\n\n@dec\ndef normalize(t):\n    return t\n\nclass A:\n    def m(self):\n        pass\n"
    c = {x.symbol: x for x in chunk_file("a.py", src)}
    assert c["normalize"].start_line == 3 and c["normalize"].chunking == "python-ast"
    assert c["A"].start_line == 7


def test_python_syntax_error_falls_back_to_lines():
    c = chunk_file("bad.py", "def broken(:\n    pass\n")
    assert c and c[0].chunking == "lines"


def test_large_python_class_split_by_method():
    body = "\n".join(f"    def m{i}(self):\n        return {i}\n" for i in range(40))
    c = chunk_file("big.py", "class Big:\n" + body)
    assert "Big.m0" in {x.symbol for x in c}


def test_brace_languages_symbols():
    js = "// helper\nexport function normalize(t) {\n  return t;\n}\n\nclass Svc {\n  async load(id) {\n    return 1;\n  }\n}\n"
    syms = {x.symbol for x in chunk_file("a.ts", js)}
    assert {"normalize", "Svc", "Svc.load"} <= syms
    java = "public class Foo {\n    public String bar(String s) {\n        return s;\n    }\n}\n"
    assert "Foo.bar" in {x.symbol for x in chunk_file("Foo.java", java)}


def test_unknown_language_uses_lines():
    assert chunk_file("q.sql", "select 1;\nselect 2;")[0].chunking == "lines"


def test_line_numbers_preserved_for_every_chunk():
    src = "a = 1\n\n\ndef f():\n    return 2\n\n\nb = 3\n"
    lines = src.splitlines()
    for c in chunk_file("x.py", src):
        assert c.content == "\n".join(lines[c.start_line - 1:c.end_line])
