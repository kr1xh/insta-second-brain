import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep  # noqa: E402

REEL = dict(source="https://www.instagram.com/x/reel/Abc/", creator="x", collection="Hooks", kind="reel")


def test_parse_collections_skips_page_link_and_duplicates():
    rows = [
        {"href": "/me/saved/", "text": ""},
        {"href": "/me/saved/all-posts/", "text": "All posts"},
        {"href": "/me/saved/cold-email/123/", "text": "Cold email"},
        {"href": "/me/saved/cold-email/123/", "text": "Cold email"},
        {"href": "/me/saved/hooks/456/", "text": "Hooks"},
    ]
    cols = sweep.parse_collections(rows)
    assert [c["name"] for c in cols] == ["Cold email", "Hooks"]
    assert cols[0] == {"name": "Cold email", "slug": "cold-email", "id": "123"}


def test_area_for_is_case_insensitive_and_defaults_to_inbox():
    mapping = {"cold email": "Internships and Research"}
    assert sweep.area_for("Cold Email", mapping) == "Internships and Research"
    assert sweep.area_for("Unknown", mapping) == sweep.INBOX


def test_safe_name_strips_path_characters():
    assert sweep.safe_name('a/b:c*"d') == "a b c d"


def test_shortcode_from_href():
    assert sweep.shortcode_from_href("/someone/reel/Abc123/") == "Abc123"


def test_screen_text_dedupes_and_puts_persistent_first():
    md = (
        'Persistent on-screen text (≥50% of the video): "Brand" | "Watermark"\n'
        '- **#1** [00:00.0–00:01.0] · text: "Hello" | "World" · speech: "hi"\n'
        '- **#2** [00:01.0–00:02.0] · text: "World" | "Again"\n'
    )
    assert sweep.screen_text(md) == ["Brand", "Watermark", "Hello", "World", "Again"]


def test_render_note_marks_video_analysis_pending():
    note = sweep.render_note(**REEL, caption="cap", likes=5, images=0, has_video=True)
    assert note.startswith("---\ntype: saved-post\n")
    assert "folder: Hooks" in note and "status: raw" in note
    assert note.count(sweep.PENDING) == 2
    assert "5 likes at capture" in note


def test_render_note_for_image_post_has_nothing_pending():
    note = sweep.render_note(source="https://www.instagram.com/p/Abc/", creator="x", collection="Hooks",
                             kind="post", caption="", likes=None, images=3, has_video=False)
    assert sweep.PENDING not in note
    assert "3 image slide(s) saved" in note and "(no video)" in note


def test_fill_analysis_replaces_markers():
    note = sweep.render_note(**REEL, caption="", likes=None, images=0, has_video=True)
    filled = sweep.fill_analysis(note, ["Title card"], "hello there")
    assert sweep.PENDING not in filled
    assert "## What's shown\n- Title card" in filled
    assert "## What's said\nhello there" in filled
    assert "(no usable speech)" in sweep.fill_analysis(note, [], "")


def test_keep_speech_drops_music_hallucinations():
    langs = {"en", "hi"}
    assert sweep.keep_speech({"speech_detected": True, "language": "en", "language_probability": 0.99}, langs)
    assert not sweep.keep_speech({"speech_detected": True, "language": "ko", "language_probability": 0.6}, langs)
    assert not sweep.keep_speech({"speech_detected": True, "language": "en", "language_probability": 0.4}, langs)
    assert not sweep.keep_speech({"speech_detected": False, "language": "en", "language_probability": 1}, langs)


def test_add_also_in_records_other_collections_once():
    note = "---\ntype: saved-post\nfolder: Hooks\nstatus: raw\n---\n"
    once = sweep.add_also_in(note, "Cool Reels")
    assert "folder: Hooks\nalso_in: [Cool Reels]" in once
    twice = sweep.add_also_in(once, "Editing Tips")
    assert "also_in: [Cool Reels, Editing Tips]" in twice
    assert sweep.add_also_in(twice, "Cool Reels") == twice
    assert sweep.add_also_in(note, "Hooks") == note


def test_index_notes_finds_shortcode_after_rename(tmp_path):
    (tmp_path / "AI-ML").mkdir()
    (tmp_path / "AI-ML" / "Nice Title.md").write_text(
        "---\nsource: https://www.instagram.com/x/reel/Abc123/\n---\n", encoding="utf-8")
    (tmp_path / "AI-ML" / "y - Def456.md").write_text(
        "---\nsource: https://www.instagram.com/p/Def456/\n---\n", encoding="utf-8")
    idx = sweep.index_notes(tmp_path)
    assert idx["Abc123"].name == "Nice Title.md" and idx["Def456"].name == "y - Def456.md"


def test_is_blocked_url():
    assert sweep.is_blocked_url("https://www.instagram.com/challenge/abc/")
    assert sweep.is_blocked_url("https://www.instagram.com/accounts/login/?next=/")
    assert not sweep.is_blocked_url("https://www.instagram.com/me/saved/")


def test_analyse_cache_deletes_video_and_frames(tmp_path, monkeypatch):
    post = tmp_path / "Abc"
    out = post / "map00"
    (out / "scan").mkdir(parents=True)
    (out / "scan" / "s1.jpg").write_bytes(b"x")
    (post / "00.mp4").write_bytes(b"x")
    (out / "video_map.md").write_text('- **#1** [0–1] · text: "Hook line"\n', encoding="utf-8")
    (out / "transcript.txt").write_text("[0-1] hi", encoding="utf-8")
    (out / "transcript.json").write_text(
        '{"speech_detected": true, "language": "en", "language_probability": 0.95}', encoding="utf-8")
    monkeypatch.setattr(sweep, "run_doughrun", lambda *a: True)
    texts, speech = sweep.analyse_cache(post, "ig.py", "small", {"en"})
    assert texts == ["Hook line"] and "hi" in speech
    assert not (post / "00.mp4").exists() and not (out / "scan").exists()
    assert (out / "video_map.md").exists()


def test_analyse_cache_failure_keeps_video(tmp_path, monkeypatch):
    post = tmp_path / "Abc"
    post.mkdir()
    (post / "00.mp4").write_bytes(b"x")
    monkeypatch.setattr(sweep, "run_doughrun", lambda *a: False)
    assert sweep.analyse_cache(post, "ig.py", "small", {"en"}) is None
    assert (post / "00.mp4").exists()
