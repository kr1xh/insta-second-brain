import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep  # noqa: E402


def test_parse_grid_extracts_code_creator_and_alt_once():
    rows = [
        {"href": "/alice/reel/Abc1/", "alt": "Photo by Alice. May be an image of text that says 'RAG in 5 steps'"},
        {"href": "/alice/reel/Abc1/", "alt": "duplicate"},
        {"href": "/p/Def2/", "alt": ""},
    ]
    assert sweep.parse_grid(rows) == [
        {"code": "Abc1", "creator": "alice", "alt": "Photo by Alice. May be an image of text that says 'RAG in 5 steps'"},
        {"code": "Def2", "creator": "", "alt": ""},
    ]


def test_triage_table_has_one_row_per_post_with_blank_decision():
    table = sweep.render_triage("Cold email", [
        {"code": "Abc1", "creator": "alice", "alt": "a | b\nc"},
    ])
    assert "folder: Cold email" in table
    row = [line for line in table.splitlines() if "Abc1" in line][0]
    assert row.startswith("|  | ")
    assert "a / b c" in row  # pipes and newlines cannot break the table


def test_read_picks_returns_only_keep_rows():
    table = "\n".join([
        "| decision | post | creator | preview |",
        "|---|---|---|---|",
        "| keep | [Abc1](https://www.instagram.com/p/Abc1/) | alice | x |",
        "| skip | [Def2](https://www.instagram.com/p/Def2/) | bob | y |",
        "| KEEP | [Ghi3](https://www.instagram.com/p/Ghi3/) | carol | z |",
        "|  | [Jkl4](https://www.instagram.com/p/Jkl4/) | dan | w |",
    ])
    assert sweep.read_picks(table) == {"Abc1", "Ghi3"}


def test_triage_marks_already_captured_posts():
    table = sweep.render_triage("Hooks", [{"code": "Abc1", "creator": "a", "alt": ""}], done={"Abc1"})
    row = [line for line in table.splitlines() if "Abc1" in line][0]
    assert row.startswith("| captured | ")


def test_select_todo_respects_done_picks_and_limit():
    hrefs = ["/a/p/A/", "/b/reel/B/", "/c/p/C/", "/d/p/D/"]
    assert sweep.select_todo(hrefs, done={"A"}, picks=None, limit=2) == ["/b/reel/B/", "/c/p/C/"]
    assert sweep.select_todo(hrefs, done=set(), picks={"D", "B"}, limit=5) == ["/b/reel/B/", "/d/p/D/"]
    assert sweep.select_todo(hrefs, done={"B"}, picks={"D", "B"}, limit=5) == ["/d/p/D/"]
