"""Capture Instagram saved collections into raw notes in an Obsidian vault.

Two stages, so the browser is never open while the heavy analysis runs:

  capture   read-only browser pass: download media and write raw notes (fast, paced)
  analyse   offline pass: OCR + transcript per video, fill in the notes, delete bulky files

Run with the Python from the instagram-mcp virtualenv (it provides instagram_sdk):

  venv\\Scripts\\python scripts/sweep.py collections --handle HANDLE [--counts]
  venv\\Scripts\\python scripts/sweep.py capture --handle HANDLE --collection "Cold email" \\
      --vault "C:\\path\\to\\vault" --map folder-map.json --limit 20
  venv\\Scripts\\python scripts/sweep.py analyse --vault "C:\\path\\to\\vault" --ig-py path\\to\\ig.py

Media and analysis live in the state directory, never in git or the vault.
"""
import argparse
import asyncio
import json
import random
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

AREA_ROOT = "Instagram Brain"
INBOX = "Inbox"
PENDING = "<!-- analysis pending -->"
DEFAULT_STATE = Path.home() / ".insta-second-brain"
SESSION_DIR = Path.home() / ".instagram-mcp" / "sessions"
BLOCKED_MARKERS = ("/challenge", "/accounts/login", "/accounts/suspended", "/accounts/disabled")

COLLECTION_JS = r"""() => [...document.querySelectorAll('a[href*="/saved/"]')]
  .map(a => ({href: a.getAttribute('href'), text: (a.innerText || '').trim().replace(/\n+/g, ' ')}))"""
POST_JS = r"""() => [...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')]
  .map(a => a.getAttribute('href'))"""


class Blocked(RuntimeError):
    """Instagram showed a login, challenge or suspension page."""


# ---------- pure helpers ----------

def safe_name(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]+', " ", text).strip(" .")[:120]


def parse_collections(rows: list[dict]) -> list[dict]:
    """Turn saved-page anchors into {name, slug, id}, skipping the page's own link."""
    out, seen = [], set()
    for row in rows:
        parts = row["href"].strip("/").split("/")
        if len(parts) < 4 or parts[1] != "saved" or not row["text"]:
            continue
        if parts[3] in seen:
            continue
        seen.add(parts[3])
        out.append({"name": row["text"], "slug": parts[2], "id": parts[3]})
    return out


def area_for(collection: str, mapping: dict[str, str]) -> str:
    return mapping.get(collection.casefold(), INBOX)


def shortcode_from_href(href: str) -> str:
    return href.strip("/").split("/")[-1]


def is_blocked_url(url: str) -> bool:
    return any(marker in url for marker in BLOCKED_MARKERS)


def screen_text(video_map_md: str, cap: int = 60) -> list[str]:
    """Unique on-screen text fragments from a doughrun video map, persistent text first."""
    def split(text: str) -> list[str]:
        return [p.strip().strip('"') for p in text.split('" | "') if p.strip().strip('"')]

    found: list[str] = []
    persistent = re.search(r"Persistent on-screen text.*?: (.*)", video_map_md)
    if persistent:
        found += split(persistent.group(1))
    for match in re.finditer(r"text: (.*?)(?: · speech:|$)", video_map_md, re.M):
        for part in split(match.group(1)):
            if part not in found:
                found.append(part)
    return found[:cap]


def keep_speech(meta: dict, langs: set[str], min_prob: float = 0.8) -> bool:
    """Whisper invents speech from music; keep a transcript only when it looks real."""
    return bool(meta.get("speech_detected")) and meta.get("language") in langs \
        and float(meta.get("language_probability") or 0) >= min_prob


def render_note(*, source, creator, collection, kind, caption, likes, images, has_video):
    shown = [PENDING] if has_video else ["(no on-screen text found)"]
    if images:
        shown.append(f"\n{images} image slide(s) saved but not read yet.")
    lines = [
        "---", "type: saved-post", f"source: {source}", f'creator: "@{creator}"', f"folder: {collection}",
        f"kind: {kind}", f"captured: {date.today().isoformat()}", "status: raw", "tags: []", "---",
        f"# {creator} - {shortcode_from_href(source)}", "", "> [!summary]", "> Raw capture, not yet distilled.", "",
        "## What's shown", *shown, "",
        "## What's said", PENDING if has_video else "(no video)", "",
        "## Caption and comments", caption.strip() if caption else "(no caption)", "",
    ]
    if likes is not None:
        lines.append(f"{likes} likes at capture. Comments not read.")
    lines += ["", "## Why it matters", "(fill in when distilled)", "", "## Related", "- [[Instagram Brain]]", ""]
    return "\n".join(lines)


def fill_analysis(note: str, texts: list[str], transcript: str) -> str:
    """Replace the two pending markers with the analysis results."""
    shown = "\n".join(f"- {t}" for t in texts) or "(no on-screen text found)"
    said = transcript.strip() or "(no usable speech)"
    note = note.replace(f"## What's shown\n{PENDING}", f"## What's shown\n{shown}", 1)
    return note.replace(f"## What's said\n{PENDING}", f"## What's said\n{said}", 1)


def add_also_in(note: str, collection: str) -> str:
    """Record that a post is saved in another collection too. No-op if already recorded."""
    folder = re.search(r"^folder: (.*)$", note, re.M)
    if folder and folder.group(1).strip() == collection:
        return note
    also = re.search(r"^also_in: \[(.*)\]$", note, re.M)
    if also:
        items = [i.strip() for i in also.group(1).split(",") if i.strip()]
        if collection in items:
            return note
        return note.replace(also.group(0), f"also_in: [{', '.join(items + [collection])}]", 1)
    if folder:
        return note.replace(folder.group(0), f"{folder.group(0)}\nalso_in: [{collection}]", 1)
    return note


def index_notes(area_root: Path) -> dict[str, Path]:
    """shortcode -> note path, read from each note's source line (survives renames)."""
    found = {}
    for p in area_root.rglob("*.md"):
        m = re.search(r"^source: \S*/(?:p|reel)/([^/\s]+)/?", p.read_text(encoding="utf-8"), re.M)
        if m:
            found[m.group(1)] = p
    return found


# ---------- state ----------

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# ---------- browser stages ----------

async def open_browser(handle: str):
    from instagram_sdk.browser import BrowserSession
    return BrowserSession(SESSION_DIR / f"{handle}_instagram_state.json", idle_timeout_s=0, headless=False)


async def goto(page, url: str) -> None:
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)
    if is_blocked_url(page.url):
        raise Blocked(page.url)


async def collect_links(page, js: str, want: int | None, scrolls: int = 40) -> list:
    seen: dict = {}
    stale = 0
    for _ in range(scrolls):
        before = len(seen)
        for item in await page.evaluate(js):
            seen.setdefault(json.dumps(item) if isinstance(item, dict) else item, item)
        if want and len(seen) >= want:
            break
        stale = stale + 1 if len(seen) == before else 0
        if stale >= 3:
            break
        await page.mouse.wheel(0, 1200)
        await page.wait_for_timeout(1800)
    return list(seen.values())


async def list_collections(page, handle: str) -> list[dict]:
    await goto(page, f"https://www.instagram.com/{handle}/saved/")
    return parse_collections(await collect_links(page, COLLECTION_JS, None, scrolls=12))


async def cmd_collections(args) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    browser = await open_browser(args.handle)
    try:
        async with browser.page() as page:
            cols = await list_collections(page, args.handle)
            if args.counts:
                for c in cols:
                    await goto(page, f"https://www.instagram.com/{args.handle}/saved/{c['slug']}/{c['id']}/")
                    c["posts"] = len(await collect_links(page, POST_JS, None, scrolls=args.max_scrolls))
                    print(f"{c['name']}\t{c['posts']}", flush=True)
                    await asyncio.sleep(random.uniform(args.pause_min, args.pause_max))
                save_json(state_dir / "collections.json", {"collections": cols})
            else:
                for c in cols:
                    print(f"{c['name']}\t{c['id']}")
    except Blocked as e:
        print(f"STOPPED: Instagram showed {e}. Do not retry today.", file=sys.stderr)
        return 4
    finally:
        await browser.shutdown()
    return 0


async def cmd_capture(args) -> int:
    import httpx
    from instagram_sdk.downloader import extension_from_url, fetch_bytes, is_downloadable_media_url
    from instagram_sdk.endpoints import post as post_ep

    mapping = {k.casefold(): v for k, v in load_json(Path(args.map)).items()}
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "sweep_state.json"
    state = load_json(state_path)
    done = set(state.get(args.collection, []))
    area_root = Path(args.vault) / AREA_ROOT
    target = area_root / area_for(args.collection, mapping)
    target.mkdir(parents=True, exist_ok=True)
    existing = index_notes(area_root)

    browser = await open_browser(args.handle)
    written = linked = 0
    try:
        async with browser.page() as page:
            match = [c for c in await list_collections(page, args.handle)
                     if c["name"].casefold() == args.collection.casefold()]
            if not match:
                print(f"collection not found: {args.collection}", file=sys.stderr)
                return 2
            await goto(page, f"https://www.instagram.com/{args.handle}/saved/{match[0]['slug']}/{match[0]['id']}/")
            hrefs = await collect_links(page, POST_JS, args.limit + len(done))
        todo = [h for h in hrefs if shortcode_from_href(h) not in done][: args.limit]
        print(f"{args.collection}: {len(hrefs)} links seen, {len(todo)} to capture -> {target.name}", flush=True)

        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            for i, href in enumerate(todo, 1):
                code = shortcode_from_href(href)
                if code in existing:
                    note = existing[code]
                    note.write_text(add_also_in(note.read_text(encoding="utf-8"), args.collection), encoding="utf-8")
                    linked += 1
                    print(f"[{i}/{len(todo)}] {code} already captured, linked", flush=True)
                else:
                    async with browser.page() as page:
                        post = await post_ep.fetch(page, id_or_url=code)
                        if is_blocked_url(page.url):
                            raise Blocked(page.url)
                    if post is None:
                        print(f"[{i}/{len(todo)}] {code} could not be loaded, skipped", flush=True)
                        continue
                    cache = state_dir / "cache" / code
                    cache.mkdir(parents=True, exist_ok=True)
                    images = videos = 0
                    for j, m in enumerate(post.media):
                        url = m.video_url or m.image_url
                        if not url or not is_downloadable_media_url(url):
                            continue
                        res = await fetch_bytes(client, url, max_bytes=None if m.video_url else 15_000_000)
                        if not res.ok:
                            continue
                        ext = "mp4" if m.video_url else (extension_from_url(url) or "jpg")
                        (cache / f"{j:02d}.{ext}").write_bytes(res.data)
                        videos += bool(m.video_url)
                        images += not m.video_url
                    creator = post.author.username if post.author else "unknown"
                    note = target / f"{safe_name(creator)} - {code}.md"
                    if not note.exists():
                        note.write_text(render_note(
                            source=post.url, creator=creator, collection=args.collection,
                            kind="reel" if videos else "post", caption=post.caption or "",
                            likes=post.like_count, images=images, has_video=bool(videos)), encoding="utf-8")
                        existing[code] = note
                        written += 1
                    print(f"[{i}/{len(todo)}] {code} {creator} ({videos} video, {images} image)", flush=True)
                done.add(code)
                state[args.collection] = sorted(done)
                save_json(state_path, state)
                if i < len(todo):
                    await asyncio.sleep(random.uniform(args.pause_min, args.pause_max))
    except Blocked as e:
        print(f"STOPPED: Instagram showed {e}. Progress is saved. Do not retry today.", file=sys.stderr)
        return 4
    finally:
        await browser.shutdown()
    print(f"done: {written} new note(s), {linked} linked to existing notes. Run 'analyse' next.")
    return 0


# ---------- offline stage ----------

def run_doughrun(ig_py: str, video: Path, out: Path, model: str) -> bool:
    out.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(["uv", "run", ig_py, "video", str(video), "--out", str(out), "--model", model],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run.returncode == 0 and (out / "video_map.md").exists()


def analyse_cache(post_dir: Path, ig_py: str, model: str, langs: set[str]) -> tuple[list[str], str] | None:
    """Analyse every video in one post's cache folder, then delete the bulky files."""
    texts: list[str] = []
    speech: list[str] = []
    for video in sorted(post_dir.glob("*.mp4")):
        out = post_dir / f"map{video.stem}"
        if not (out / "video_map.md").exists() and not run_doughrun(ig_py, video, out, model):
            return None
        texts += [t for t in screen_text((out / "video_map.md").read_text(encoding="utf-8")) if t not in texts]
        meta = load_json(out / "transcript.json")
        transcript = out / "transcript.txt"
        if transcript.exists() and keep_speech(meta, langs):
            speech.append(transcript.read_text(encoding="utf-8"))
        video.unlink()
        shutil.rmtree(out / "scan", ignore_errors=True)
    return texts, "\n".join(speech)


def cmd_analyse(args) -> int:
    state_dir = Path(args.state_dir)
    notes = index_notes(Path(args.vault) / AREA_ROOT)
    langs = {code.strip() for code in args.langs.split(",") if code.strip()}
    pending = [d for d in sorted((state_dir / "cache").glob("*")) if d.is_dir() and any(d.glob("*.mp4"))]
    pending = pending[: args.limit] if args.limit else pending
    print(f"{len(pending)} post(s) with videos to analyse", flush=True)
    for i, post_dir in enumerate(pending, 1):
        result = analyse_cache(post_dir, args.ig_py, args.whisper_model, langs)
        if result is None:
            print(f"[{i}/{len(pending)}] {post_dir.name} analysis failed, kept for retry", flush=True)
            continue
        note = notes.get(post_dir.name)
        if note and PENDING in (text := note.read_text(encoding="utf-8")):
            note.write_text(fill_analysis(text, *result), encoding="utf-8")
        print(f"[{i}/{len(pending)}] {post_dir.name} done", flush=True)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def paced(sp):
        sp.add_argument("--handle", required=True)
        sp.add_argument("--state-dir", default=str(DEFAULT_STATE))
        sp.add_argument("--pause-min", type=float, default=12)
        sp.add_argument("--pause-max", type=float, default=25)

    c = sub.add_parser("collections", help="list collections; --counts also counts posts in each")
    paced(c)
    c.add_argument("--counts", action="store_true")
    c.add_argument("--max-scrolls", type=int, default=60)

    cap = sub.add_parser("capture", help="download one collection and write raw notes")
    paced(cap)
    cap.add_argument("--collection", required=True)
    cap.add_argument("--vault", required=True)
    cap.add_argument("--map", required=True, help="JSON file: collection name -> area folder")
    cap.add_argument("--limit", type=int, default=20)

    an = sub.add_parser("analyse", help="offline OCR + transcript for captured videos")
    an.add_argument("--vault", required=True)
    an.add_argument("--ig-py", required=True, help="path to doughrun's ig.py")
    an.add_argument("--state-dir", default=str(DEFAULT_STATE))
    an.add_argument("--whisper-model", default="small", help="smaller models use less memory")
    an.add_argument("--langs", default="en,hi", help="transcript languages to keep")
    an.add_argument("--limit", type=int, default=0, help="0 = all pending")

    args = p.parse_args(argv)
    if args.cmd == "analyse":
        return cmd_analyse(args)
    return asyncio.run(cmd_collections(args) if args.cmd == "collections" else cmd_capture(args))


if __name__ == "__main__":
    sys.exit(main())
