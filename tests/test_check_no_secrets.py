import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_no_secrets as cns  # noqa: E402


def run(paths, contents=None):
    contents = contents or {}
    return cns.check(paths, read=lambda p: contents.get(p, b"hello"))


def test_clean_files_pass():
    assert run(["README.md", "scripts/x.py"]) == []


def test_session_and_cookie_paths_blocked():
    for p in ["sessions/me.json", "a/storage_state.json", "x_instagram_state.json", "cookies.json", ".env"]:
        assert run([p]), p


def test_env_example_allowed():
    assert run([".env.example"]) == []


def test_media_and_vault_blocked():
    assert run(["clip.mp4"])
    assert run(["8 - Instagram Second Brain/01-ai-ml-projects/a.md"])


def test_sessionid_in_content_blocked():
    assert run(["notes.txt"], {"notes.txt": b"sessionid=abcdefghijklmnopqrstuvwx1234"})


def test_short_placeholder_ok():
    assert run(["doc.md"], {"doc.md": b"copy the sessionid cookie value"}) == []
