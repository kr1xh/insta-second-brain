import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import weekly  # noqa: E402


def test_allocate_fills_folders_in_priority_order():
    remaining = {"Interships": 43, "AI/ML PROJECTS": 30, "DSA": 3}
    assert weekly.allocate(["Interships", "AI/ML PROJECTS", "DSA"], remaining, 10) == [("Interships", 10)]


def test_allocate_spills_over_when_a_folder_runs_out():
    remaining = {"Hackathons & Competition": 4, "DSA": 3, "Reels": 20}
    assert weekly.allocate(["Hackathons & Competition", "DSA", "Reels"], remaining, 10) == [
        ("Hackathons & Competition", 4), ("DSA", 3), ("Reels", 3)]


def test_allocate_skips_finished_folders_and_unknown_counts_go_last():
    remaining = {"Cold email": 0, "All about Quant": None, "Interships": 2}
    assert weekly.allocate(["Cold email", "All about Quant", "Interships"], remaining, 10) == [
        ("Interships", 2), ("All about Quant", 8)]


def test_remaining_keeps_counts_keep_rows_not_yet_captured(tmp_path):
    tri = tmp_path / "Instagram Brain" / "Triage"
    tri.mkdir(parents=True)
    (tri / "DSA.md").write_text(
        "| keep | [A1](x) | a | b |\n| keep | [A2](x) | a | b |\n| skip | [A3](x) | a | b |\n| captured | [A4](x) | a | b |\n",
        encoding="utf-8")
    state = {"DSA": ["A1"]}
    assert weekly.remaining_keeps(tmp_path, ["DSA", "No table"], state) == {"DSA": 1, "No table": None}
