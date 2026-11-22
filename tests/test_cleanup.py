import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cleanup  # noqa: E402


def populate(home):
    (home / ".instagram-mcp" / "sessions").mkdir(parents=True)
    (home / ".instagram-mcp" / "sessions" / "x_instagram_state.json").write_text("{}")
    (home / ".insta-second-brain" / "cache" / "abc").mkdir(parents=True)
    (home / ".insta-second-brain" / "sweep_state.json").write_text("{}")


def test_dry_run_deletes_nothing(tmp_path):
    populate(tmp_path)
    cleanup.run(tmp_path, yes=False, include_state=False)
    assert (tmp_path / ".instagram-mcp" / "sessions").exists()


def test_yes_removes_sessions_and_cache_but_keeps_state(tmp_path):
    populate(tmp_path)
    cleanup.run(tmp_path, yes=True, include_state=False)
    assert not (tmp_path / ".instagram-mcp" / "sessions").exists()
    assert not (tmp_path / ".insta-second-brain" / "cache").exists()
    assert (tmp_path / ".insta-second-brain" / "sweep_state.json").exists()


def test_include_state_removes_progress(tmp_path):
    populate(tmp_path)
    cleanup.run(tmp_path, yes=True, include_state=True)
    assert not (tmp_path / ".insta-second-brain" / "sweep_state.json").exists()


def test_nothing_to_remove(tmp_path):
    assert cleanup.run(tmp_path, yes=True, include_state=True) == 0
