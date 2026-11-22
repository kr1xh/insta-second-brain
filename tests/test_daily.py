import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import weekly  # noqa: E402


def test_remaining_keeps_counts_keep_rows_not_yet_captured(tmp_path):
    tri = tmp_path / "Instagram Brain" / "Triage"
    tri.mkdir(parents=True)
    (tri / "DSA.md").write_text(
        "| keep | [A1](x) | a | b |\n| keep | [A2](x) | a | b |\n| skip | [A3](x) | a | b |\n| captured | [A4](x) | a | b |\n",
        encoding="utf-8")
    state = {"DSA": ["A1"]}
    assert weekly.remaining_keeps(tmp_path, ["DSA", "No table"], state) == {"DSA": 1, "No table": None}


def _tables(tmp_path, rows: dict[str, list[str]]):
    tri = tmp_path / "Instagram Brain" / "Triage"
    tri.mkdir(parents=True, exist_ok=True)
    for name, codes in rows.items():
        (tri / f"{name}.md").write_text("".join(f"| keep | [{c}](x) | a | b |\n" for c in codes), encoding="utf-8")


def test_run_daily_passes_unused_budget_on_when_a_folder_is_stuck(tmp_path):
    _tables(tmp_path, {"Stuck": ["S1", "S2"], "Next": [f"N{i}" for i in range(20)]})
    state = {}
    calls = []

    def runner(cmd):
        name = cmd[cmd.index("--collection") + 1] if "--collection" in cmd else "analyse"
        limit = int(cmd[cmd.index("--limit") + 1]) if "--limit" in cmd else 0
        calls.append((name, limit))
        if name == "Next":  # Stuck captures nothing (deleted posts); Next captures what it is asked for
            state.setdefault("Next", []).extend(f"N{i}" for i in range(limit))
        return 0

    cfg = {"python": "py", "handle": "me", "vault": str(tmp_path), "map": "m", "ig_py": "ig",
           "collections": ["Stuck", "Next"], "daily_total": 10}
    assert weekly.run_daily(cfg, runner, lambda: state) == 0
    assert calls == [("Stuck", 2), ("Next", 10), ("analyse", 0)]


def test_run_daily_stops_on_a_challenge_page(tmp_path):
    _tables(tmp_path, {"A": ["A1"], "B": ["B1"]})
    cfg = {"python": "py", "handle": "me", "vault": str(tmp_path), "map": "m", "ig_py": "ig",
           "collections": ["A", "B"], "daily_total": 10}
    seen = []
    assert weekly.run_daily(cfg, lambda cmd: seen.append(cmd) or 4, lambda: {}) == 4
    assert len(seen) == 1
