from app.stacktrace import parse_stack_refs, path_matches


def test_python_trace():
    refs = parse_stack_refs('  File "/app/utils/text.py", line 2, in normalize\nAttributeError')
    assert refs[0].file == "/app/utils/text.py" and refs[0].line == 2 and refs[0].func == "normalize" and refs[0].top


def test_js_java_go_cs():
    t = ("at normalize (/srv/app/text.js:12:5)\nat com.acme.Text.normalize(Text.java:42)\n"
         "main.go:25 +0x1d\nat Ns.C.M() in C:\\src\\File.cs:line 9")
    files = {r.file.split("/")[-1].split("\\")[-1] for r in parse_stack_refs(t)}
    assert {"text.js", "Text.java", "main.go", "File.cs"} <= files


def test_top_frame_python_last_others_first():
    py = parse_stack_refs('File "a.py", line 1, in main\nFile "b.py", line 2, in inner')
    assert [r.top for r in py] == [False, True]
    js = parse_stack_refs("at inner (b.js:2:1)\nat main (a.js:1:1)")
    assert [r.top for r in js] == [True, False]


def test_urls_with_ports_are_not_refs():
    assert parse_stack_refs("could not reach example.com:8080 and localhost:3000") == []


def test_path_matching():
    assert path_matches("app/utils/text.py", "/home/u/proj/app/utils/text.py")
    assert path_matches("app/utils/text.py", "text.py")
    assert not path_matches("app/utils/text.py", "other/text2.py")
