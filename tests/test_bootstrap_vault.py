import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import bootstrap_vault as bv  # noqa: E402


def test_creates_area(tmp_path):
    assert bv.main(["--vault", str(tmp_path)]) == 0
    root = tmp_path / bv.ROOT_NAME
    assert (root / f"{bv.ROOT_NAME}.md").is_file()
    assert (root / "Inbox").is_dir()
    assert (root / "Drafts").is_dir()
    assert (root / "AI-ML Projects").is_dir()
    assert (tmp_path / "Templates" / "Saved Post.md").is_file()


def test_dry_run_writes_nothing(tmp_path):
    assert bv.main(["--vault", str(tmp_path), "--dry-run"]) == 0
    assert list(tmp_path.iterdir()) == []


def test_never_overwrites(tmp_path):
    (tmp_path / "Templates").mkdir()
    tpl = tmp_path / "Templates" / "Saved Post.md"
    tpl.write_text("mine", encoding="utf-8")
    bv.main(["--vault", str(tmp_path)])
    assert tpl.read_text(encoding="utf-8") == "mine"


def test_does_not_touch_other_vault_files(tmp_path):
    other = tmp_path / "Home.md"
    other.write_text("keep", encoding="utf-8")
    bv.main(["--vault", str(tmp_path)])
    assert other.read_text(encoding="utf-8") == "keep"


def test_missing_vault_errors(tmp_path):
    assert bv.main(["--vault", str(tmp_path / "nope")]) == 2
