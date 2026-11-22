import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import install_commands as ic  # noqa: E402


def test_installs_with_vault_path_filled_in(tmp_path):
    done = ic.install("C:/vault", tmp_path)
    assert {"ig-query.md", "ig-draft.md", "ig-distill.md", "ig-promote.md", "ig-week.md", "ig-gapfill.md"} <= set(done)
    assert "{{VAULT}}" not in (tmp_path / "ig-query.md").read_text(encoding="utf-8")
    assert "C:/vault/Instagram Brain" in (tmp_path / "ig-query.md").read_text(encoding="utf-8")


def test_does_not_overwrite_without_force(tmp_path):
    (tmp_path / "ig-query.md").write_text("mine", encoding="utf-8")
    ic.install("v", tmp_path)
    assert (tmp_path / "ig-query.md").read_text(encoding="utf-8") == "mine"
    ic.install("v", tmp_path, force=True)
    assert (tmp_path / "ig-query.md").read_text(encoding="utf-8") != "mine"
