"""Remove login sessions, downloaded media and sweep caches. Dry run unless --yes is given.

Never touches your vault or notes.
Usage: python scripts/cleanup.py [--yes] [--include-state]
"""
import argparse
import shutil
import sys
from pathlib import Path


def targets(home: Path, include_state: bool) -> list[Path]:
    found = [
        home / ".instagram-mcp" / "sessions",
        home / ".instagram-mcp" / "downloads",
        home / ".insta-second-brain" / "cache",
    ]
    if include_state:
        found += [home / ".insta-second-brain" / "sweep_state.json", home / ".insta-second-brain" / "folder-map.json"]
    return [p for p in found if p.exists()]


def size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def run(home: Path, yes: bool, include_state: bool) -> int:
    paths = targets(home, include_state)
    if not paths:
        print("nothing to remove")
        return 0
    for p in paths:
        print(f"{'remove' if yes else 'would remove'} {p} ({size(p) / 1e6:.1f} MB)")
        if yes:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    if not yes:
        print("\nDry run. Re-run with --yes to delete.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yes", action="store_true", help="actually delete")
    ap.add_argument("--include-state", action="store_true", help="also remove sweep progress and the folder map")
    ap.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    return run(args.home, args.yes, args.include_state)


if __name__ == "__main__":
    sys.exit(main())
