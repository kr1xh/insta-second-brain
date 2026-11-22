import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import vault_health as vh  # noqa: E402

GOOD = """---
type: saved-post
source: https://x
creator: "@a"
folder: Hooks
kind: reel
captured: 2026-11-22
status: {status}
---
# t
{body}
"""


def make(tmp_path):
    area = tmp_path / "Instagram Brain"
    (area / "Content Creation").mkdir(parents=True)
    (area / "Inbox").mkdir()
    return area


def test_clean_vault_has_no_problems(tmp_path):
    area = make(tmp_path)
    (area / "Instagram Brain.md").write_text("# hub\n- [[a - 1]]\n", encoding="utf-8")
    (area / "Content Creation" / "a - 1.md").write_text(GOOD.format(status="distilled", body="[[Instagram Brain]]"), encoding="utf-8")
    r = vh.check(tmp_path)
    assert r["notes"] == 1 and vh.problems(r) == 0


def test_raw_notes_need_no_index_entry(tmp_path):
    area = make(tmp_path)
    (area / "Instagram Brain.md").write_text("# hub\n", encoding="utf-8")
    (area / "Content Creation" / "a - 1.md").write_text(GOOD.format(status="raw", body=""), encoding="utf-8")
    assert vh.problems(vh.check(tmp_path)) == 0


def test_finds_broken_link_missing_field_and_unindexed(tmp_path):
    area = make(tmp_path)
    (area / "Instagram Brain.md").write_text("# hub\n", encoding="utf-8")
    (area / "Content Creation" / "a - 1.md").write_text(GOOD.format(status="distilled", body="[[Nowhere]]"), encoding="utf-8")
    (area / "Inbox" / "b - 2.md").write_text("---\ntype: saved-post\nstatus: raw\n---\n", encoding="utf-8")
    r = vh.check(tmp_path)
    assert r["broken_links"] == [("a - 1.md", "Nowhere")]
    assert r["not_in_index"] == ["a - 1.md"]
    assert r["missing_fields"][0][0] == "b - 2.md"
    assert r["in_inbox"] == ["b - 2.md"]


def test_missing_area_errors(tmp_path):
    assert vh.main(["--vault", str(tmp_path)]) == 2
