import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import weekly  # noqa: E402

CFG = {"python": "py.exe", "handle": "me", "vault": "V", "map": "m.json", "ig_py": "ig.py",
       "collections": ["Cold email", "Hooks"], "limit": 20}


def test_plan_captures_each_collection_then_analyses():
    steps = weekly.plan(CFG)
    assert [s[2] for s in steps] == ["capture", "capture", "analyse"]
    assert steps[0][steps[0].index("--collection") + 1] == "Cold email"
    assert steps[1][steps[1].index("--limit") + 1] == "20"
    assert steps[2][steps[2].index("--ig-py") + 1] == "ig.py"


def test_run_stops_everything_when_instagram_blocks():
    calls = []

    def fake(cmd):
        calls.append(cmd[2])
        return 4 if len(calls) == 1 else 0

    assert weekly.run(CFG, runner=fake) == 4
    assert calls == ["capture"]


def test_run_continues_past_other_failures_and_still_analyses():
    calls = []

    def fake(cmd):
        calls.append(cmd[2])
        return 2 if len(calls) == 1 else 0

    assert weekly.run(CFG, runner=fake) == 0
    assert calls == ["capture", "capture", "analyse"]
