"""Capture an Instagram saved collection into raw notes in an Obsidian vault.

Run with the Python from the instagram-mcp virtualenv (it provides instagram_sdk):

  venv\\Scripts\\python scripts/sweep.py collections --handle HANDLE
  venv\\Scripts\\python scripts/sweep.py run --handle HANDLE --collection "Cold email" \\
      --vault "C:\\path\\to\\vault" --map folder-map.json --limit 20

Read-only against Instagram. Posts are fetched one at a time with pauses.
Media and analysis go to the state directory, never into git or the vault.
"""
import argparse
import asyncio
import json
import random
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

AREA_ROOT = "Instagram Brain"
INBOX = "Inbox"
DEFAULT_STATE = Path.home() / ".insta-second-brain"
SESSION_DIR = Path.home() / ".instagram-mcp" / "sessions"

COLLECTION_JS = r"""() => [...document.querySelectorAll('a[href*="/saved/"]')]
  .map(a => ({href: a.getAttribute('href'), text: (a.innerText || '').trim().replace(/\n+/g, ' ')}))"""
POST_JS = r"""() => [...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')]
  .map(a => a.getAttribute('href'))"""


def safe_name(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]+', " ", text).strip(" .")[:120]


def parse_collections(rows: list[dict]) -> list[dict]:
    """Turn saved-page anchors into {name, slug, id}, skipping the page's own link."""
    out, seen = [], set()
    for row in rows:
        parts = row["href"].strip("/").split("/")
        if len(parts) < 4 or parts[1] != "saved" or not row["text"]:
            continue
        key = parts[3]
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": row["text"], "slug": parts[2], "id": parts[3]})
    return out


def area_for(collection: str, mapping: dict[str, str]) -> str:
    return mapping.get(collection.casefold(), INBOX)


def shortcode_from_href(href: str) -> str:
    return href.strip("/").split("/")[-1]


def screen_text(video_map_md: str, cap: int = 60) -> list[str]:
    """Unique on-screen text fragments from a doughrun video map, in order."""
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


def render_note(*, source, creator, collection, kind, caption, likes, texts, transcript, images):
    lines = [
        "---",
        "type: saved-post",
        f"source: {source}",
        f'creator: "@{creator}"',
        f"folder: {collection}",
        f"kind: {kind}",
        f"captured: {date.today().isoformat()}",
        "status: raw",
        "tags: []",
        "---",
        f"# {creator} - {shortcode_from_href(source)}",
        "",
        "> [!summary]",
        "> Raw capture, not yet distilled.",
        "",
        "## What's shown",
    ]
    lines += [f"- {t}" for t in texts] or ["(no on-screen text found)"]
    if images:
        lines.append(f"\n{images} image slide(s) saved but not read yet.")
    lines += ["", "## What's said", transcript.strip() or "(no speech detected)", "", "## Caption and comments"]
    lines += [caption.strip() if caption else "(no caption)", ""]
    if likes is not None:
        lines.append(f"{likes} likes at capture. Comments not read.")
    lines += ["", "## Why it matters", "(fill in when distilled)", "", "## Related", "- [[Instagram Brain]]", ""]
    return "\n".join(lines)


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


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def analyse_video(ig_py: str, video: Path, out: Path) -> tuple[list[str], str]:
    out.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(["uv", "run", ig_py, "video", str(video), "--out", str(out)],
                         capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        return [], ""
    map_md = out / "video_map.md"
    transcript = out / "transcript.txt"
    texts = screen_text(map_md.read_text(encoding="utf-8")) if map_md.exists() else []
    speech = transcript.read_text(encoding="utf-8") if transcript.exists() else ""
    return texts, speech if "no speech" not in speech.lower() else ""


async def open_browser(handle: str):
    from instagram_sdk.browser import BrowserSession
    session = SESSION_DIR / f"{handle}_instagram_state.json"
    return BrowserSession(session, idle_timeout_s=0, headless=False)


async def cmd_collections(args) -> int:
    browser = await open_browser(args.handle)
    try:
        async with browser.page() as page:
            await page.goto(f"https://www.instagram.com/{args.handle}/saved/", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            rows = await collect_links(page, COLLECTION_JS, None, scrolls=12)
        for c in parse_collections(rows):
            print(f"{c['name']}\t{c['id']}")
    finally:
        await browser.shutdown()
    return 0


async def cmd_run(args) -> int:
    import httpx
    from instagram_sdk.downloader import extension_from_url, fetch_bytes, is_downloadable_media_url
    from instagram_sdk.endpoints import post as post_ep

    mapping = {k.casefold(): v for k, v in json.loads(Path(args.map).read_text(encoding="utf-8")).items()}
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "sweep_state.json"
    state = load_state(state_path)
    done = set(state.get(args.collection, []))
    area = area_for(args.collection, mapping)
    target = Path(args.vault) / AREA_ROOT / area
    target.mkdir(parents=True, exist_ok=True)

    browser = await open_browser(args.handle)
    written = 0
    try:
        async with browser.page() as page:
            await page.goto(f"https://www.instagram.com/{args.handle}/saved/", wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            cols = parse_collections(await collect_links(page, COLLECTION_JS, None, scrolls=12))
            matches = [c for c in cols if c["name"].casefold() == args.collection.casefold()]
            if not matches:
                print(f"collection not found: {args.collection}", file=sys.stderr)
                return 2
            col = matches[0]
            url = f"https://www.instagram.com/{args.handle}/saved/{col['slug']}/{col['id']}/"
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            hrefs = await collect_links(page, POST_JS, args.limit + len(done))
        todo = [h for h in hrefs if shortcode_from_href(h) not in done][: args.limit]
        print(f"{args.collection}: {len(hrefs)} links seen, {len(todo)} to capture -> {area}")

        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            for i, href in enumerate(todo, 1):
                code = shortcode_from_href(href)
                async with browser.page() as page:
                    post = await post_ep.fetch(page, id_or_url=code)
                if post is None:
                    print(f"[{i}/{len(todo)}] {code} could not be loaded, skipped")
                    continue
                cache = state_dir / "cache" / code
                cache.mkdir(parents=True, exist_ok=True)
                texts, speech, images, kind = [], "", 0, "post"
                for j, m in enumerate(post.media):
                    media_url = m.video_url or m.image_url
                    if not media_url or not is_downloadable_media_url(media_url):
                        continue
                    res = await fetch_bytes(client, media_url, max_bytes=None if m.video_url else 15_000_000)
                    if not res.ok:
                        continue
                    if m.video_url:
                        kind = "reel"
                        file = cache / f"{j:02d}.mp4"
                        file.write_bytes(res.data)
                        t, s = analyse_video(args.ig_py, file, cache / f"map{j:02d}")
                        texts += t
                        speech += s
                    else:
                        (cache / f"{j:02d}.{extension_from_url(media_url) or 'jpg'}").write_bytes(res.data)
                        images += 1
                creator = post.author.username if post.author else "unknown"
                note = target / f"{safe_name(creator)} - {code}.md"
                if not note.exists():
                    note.write_text(render_note(
                        source=post.url, creator=creator, collection=args.collection, kind=kind,
                        caption=post.caption or "", likes=post.like_count, texts=texts,
                        transcript=speech, images=images), encoding="utf-8")
                    written += 1
                done.add(code)
                state[args.collection] = sorted(done)
                state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
                print(f"[{i}/{len(todo)}] {code} {creator} ({kind})", flush=True)
                if i < len(todo):
                    await asyncio.sleep(random.uniform(args.pause_min, args.pause_max))
    finally:
        await browser.shutdown()
    print(f"done: {written} note(s) written")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collections", help="print collection names and ids")
    c.add_argument("--handle", required=True)
    r = sub.add_parser("run", help="capture one collection into raw notes")
    r.add_argument("--handle", required=True)
    r.add_argument("--collection", required=True)
    r.add_argument("--vault", required=True)
    r.add_argument("--map", required=True, help="JSON file: collection name -> area folder")
    r.add_argument("--ig-py", required=True, help="path to doughrun's ig.py")
    r.add_argument("--limit", type=int, default=20)
    r.add_argument("--state-dir", default=str(DEFAULT_STATE))
    r.add_argument("--pause-min", type=float, default=12)
    r.add_argument("--pause-max", type=float, default=25)
    args = p.parse_args(argv)
    return asyncio.run(cmd_collections(args) if args.cmd == "collections" else cmd_run(args))


if __name__ == "__main__":
    sys.exit(main())
