import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sweep  # noqa: E402


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


def test_render_note_has_frontmatter_and_sections():
    note = sweep.render_note(
        source="https://www.instagram.com/x/reel/Abc/", creator="x", collection="Hooks", kind="reel",
        caption="cap", likes=5, texts=["one"], transcript="", images=0)
    assert note.startswith("---\ntype: saved-post\n")
    assert "folder: Hooks" in note and "status: raw" in note
    assert "(no speech detected)" in note and "- one" in note
    assert "5 likes at capture" in note
