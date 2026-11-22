import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep  # noqa: E402


def page(*comments):
    blob = {"require": [["x", {"data": {"comments": [
        {"pk": str(i), "text": t, "created_at": 100 + i, "user": {"username": u}} for i, (u, t) in enumerate(comments)
    ]}}]]}
    return f'<html><script type="application/json" data-sjs>{json.dumps(blob)}</script></html>'


def test_author_comments_keeps_only_the_creators_in_order():
    html = page(("alice", "Template: Dear Prof [Name]"), ("bob", "thanks!"), ("alice", "CV tips: 1-2 pages"))
    assert sweep.author_comments(html, "alice") == ["Template: Dear Prof [Name]", "CV tips: 1-2 pages"]


def test_author_comments_is_case_insensitive_and_skips_bad_json():
    html = page(("Alice", "hi")) + '<script type="application/json">{not json</script>'
    assert sweep.author_comments(html, "alice") == ["hi"]


def test_author_comments_empty_when_creator_never_commented():
    assert sweep.author_comments(page(("bob", "x")), "alice") == []


def test_render_note_includes_creator_comments():
    note = sweep.render_note(source="https://www.instagram.com/p/A/", creator="alice", collection="Cold email",
                             kind="post", caption="cap", likes=3, images=0, has_video=False,
                             creator_comments=["Dear Prof [Name]"])
    assert "Creator's comments" in note and "> Dear Prof [Name]" in note
    assert "Comments not read" not in note


NOTE = """---
type: saved-post
source: https://www.instagram.com/p/A/
status: distilled
gated: true
---
# t

## Caption and comments
Check the comments!

12 likes at capture. Comments not read.

## Why it matters
x
"""


def test_add_creator_comments_inserts_block_and_marks_checked():
    out = sweep.add_creator_comments(NOTE, ["Dear Prof [Name]"])
    assert "comments_checked: true" in out
    cap = out.split("## Caption and comments")[1].split("## Why it matters")[0]
    assert "> Dear Prof [Name]" in cap and "Check the comments!" in cap
    assert "Other comments not read." in cap


def test_add_creator_comments_with_none_found_only_marks_checked():
    out = sweep.add_creator_comments(NOTE, [])
    assert "comments_checked: true" in out and "Creator's comments" not in out


def test_needs_comments_picks_gated_or_comment_mentioning_unchecked_notes():
    assert sweep.needs_comments(NOTE)
    assert not sweep.needs_comments(sweep.add_creator_comments(NOTE, []))
    assert not sweep.needs_comments(NOTE.replace("gated: true\n", "").replace("Check the comments!", "Plain caption"))


def test_needs_comments_waits_for_pending_analysis():
    assert not sweep.needs_comments(NOTE.replace("x\n", f"{sweep.PENDING}\n"))


def test_author_comments_strips_replacement_characters():
    assert sweep.author_comments(page(("alice", "CV (1-2 pages).�")), "alice") == ["CV (1-2 pages)."]
