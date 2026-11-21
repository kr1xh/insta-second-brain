import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import bootstrap_vault as bv  # noqa: E402


def test_creates_skeleton(tmp_path):
    assert bv.main(["--vault", str(tmp_path)]) == 0
    root = tmp_path / bv.ROOT_NAME
    assert (root / "CLAUDE.md").is_file()
    assert (root / "00-meta" / "index.md").is_file()
    assert (root / "06-inbox").is_dir()
    assert (root / ".claude" / "commands").is_dir()


def test_dry_run_writes_nothing(tmp_path):
    assert bv.main(["--vault", str(tmp_path), "--dry-run"]) == 0
    assert list(tmp_path.iterdir()) == []


def test_never_overwrites(tmp_path):
    root = tmp_path / bv.ROOT_NAME
    (root / "00-meta").mkdir(parents=True)
    idx = root / "00-meta" / "index.md"
    idx.write_text("mine", encoding="utf-8")
    bv.main(["--vault", str(tmp_path)])
    assert idx.read_text(encoding="utf-8") == "mine"


def test_does_not_touch_other_vault_files(tmp_path):
    other = tmp_path / "notes.md"
    other.write_text("keep", encoding="utf-8")
    bv.main(["--vault", str(tmp_path)])
    assert other.read_text(encoding="utf-8") == "keep"


def test_missing_vault_errors(tmp_path):
    assert bv.main(["--vault", str(tmp_path / "nope")]) == 2
