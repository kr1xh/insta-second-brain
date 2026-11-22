"""Report problems in the Instagram Brain area of a vault. Read-only: nothing is changed.

Usage: python scripts/vault_health.py --vault "<path>" [--area "Instagram Brain"]
Exit code is 1 when problems are found.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ["type", "source", "creator", "folder", "kind", "captured", "status"]
LINK = re.compile(r"\[\[([^\]|#]+)")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def check(vault: Path, area: str = "Instagram Brain") -> dict:
    root = vault / area
    all_names = {p.stem for p in vault.rglob("*.md")}
    notes = [p for p in root.rglob("*.md") if frontmatter(p.read_text(encoding="utf-8")).get("type") == "saved-post"]
    hub = root / f"{area}.md"
    hub_text = hub.read_text(encoding="utf-8") if hub.exists() else ""
    linked_from_hub = set(LINK.findall(hub_text))

    report = {"notes": len(notes), "status": Counter(), "missing_fields": [], "broken_links": [],
              "not_in_index": [], "in_inbox": []}
    for note in notes:
        text = note.read_text(encoding="utf-8")
        fields = frontmatter(text)
        report["status"][fields.get("status", "?")] += 1
        missing = [f for f in REQUIRED if not fields.get(f)]
        if missing:
            report["missing_fields"].append((note.name, missing))
        for target in set(LINK.findall(text)):
            if target.strip() not in all_names:
                report["broken_links"].append((note.name, target.strip()))
        if fields.get("status") == "distilled" and note.stem not in linked_from_hub:
            report["not_in_index"].append(note.name)
        if note.parent.name == "Inbox":
            report["in_inbox"].append(note.name)
    return report


def problems(report: dict) -> int:
    return sum(len(report[k]) for k in ("missing_fields", "broken_links", "not_in_index"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--area", default="Instagram Brain")
    args = ap.parse_args(argv)
    if not (args.vault / args.area).is_dir():
        print(f"error: {args.vault / args.area} not found", file=sys.stderr)
        return 2
    r = check(args.vault, args.area)
    print(f"{r['notes']} notes; status: {dict(r['status'])}")
    for label, key in [("Missing fields", "missing_fields"), ("Broken links", "broken_links"),
                       ("Distilled but not in the hub index", "not_in_index"), ("Waiting in Inbox", "in_inbox")]:
        if r[key]:
            print(f"\n{label} ({len(r[key])}):")
            for item in r[key][:50]:
                print(f"  {item}")
    return 1 if problems(r) else 0


if __name__ == "__main__":
    sys.exit(main())
