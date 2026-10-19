from app.ignore import filter_files, ignore_reason
from app.secrets_scan import redact


def test_ignore_rules():
    assert ignore_reason("node_modules/x/index.js")
    assert ignore_reason("dist/app.js")
    assert ignore_reason("img/logo.png")
    assert ignore_reason(".env") and ignore_reason("certs/server.pem")
    assert ignore_reason("../etc/passwd") == "unsafe path"
    assert ignore_reason("a.py", "x\x00y") == "binary content"
    assert ignore_reason(".env.example") is None
    assert ignore_reason("src/app.py") is None


def test_filter_files_reports_reasons():
    kept, skipped = filter_files([("a.py", "x=1"), (".git/config", "x"), ("pkg/yarn.lock", "x")])
    assert [k[0] for k in kept] == ["a.py"] and len(skipped) == 2


def test_redaction_preserves_line_numbers():
    src = 'password = "supersecret1"\nk = "AKIAABCDEFGHIJKLMNOP"\n-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----\nz = 1'
    out, findings = redact(src)
    assert "supersecret1" not in out and "AKIA" not in out and "abc" not in out
    assert out.count("\n") == src.count("\n") and out.endswith("z = 1")
    assert [l for l, _ in findings] == [1, 2, 3]


def test_no_false_redaction_on_plain_code():
    src = "def get_token_count():\n    return 3\n"
    assert redact(src) == (src, [])
