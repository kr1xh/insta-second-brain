"""Create the Instagram Brain area inside an Obsidian vault.

Existing files and folders are never modified or overwritten.
Usage: python scripts/bootstrap_vault.py --vault "<path>" [--dry-run]
"""
import argparse
import sys
from pathlib import Path

ROOT_NAME = "Instagram Brain"
REPO = Path(__file__).resolve().parent.parent

DEFAULT_FOLDERS = [
    "AI-ML Projects",
    "Quant Projects",
    "Reels and Content",
    "Cold Emails",
    "Internships",
]
FIXED_FOLDERS = ["Inbox", "Drafts"]

# destination relative to the vault root -> template source
FILES = {
    f"{ROOT_NAME}/{ROOT_NAME}.md": REPO / "templates" / "instagram-brain.md",
    "Templates/Saved Post.md": REPO / "templates" / "saved-post.md",
}


def plan(vault: Path, folders: list[str]) -> list[tuple[str, Path, Path | None]]:
    root = vault / ROOT_NAME
    steps = [("dir", root, None)]
    for name in FIXED_FOLDERS + folders:
        steps.append(("dir", root / name, None))
    for rel, src in FILES.items():
        steps.append(("file", vault / rel, src))
    return steps


def apply(steps, dry_run: bool) -> dict[str, int]:
    counts = {"created": 0, "skipped": 0}
    for kind, path, src in steps:
        if path.exists():
            counts["skipped"] += 1
            print(f"skip    {path}")
            continue
        counts["created"] += 1
        print(f"{'would create' if dry_run else 'create'} {path}")
        if dry_run:
            continue
        if kind == "dir":
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return counts


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vault", required=True, type=Path, help="Obsidian vault root")
    p.add_argument("--folders", nargs="*", default=DEFAULT_FOLDERS,
                   help="Instagram folder names (default: the five starter folders)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not args.vault.is_dir():
        print(f"error: vault not found: {args.vault}", file=sys.stderr)
        return 2
    counts = apply(plan(args.vault, args.folders), args.dry_run)
    print(f"\n{counts['created']} to create, {counts['skipped']} already existed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
