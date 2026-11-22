"""Copy the slash commands to a Claude Code commands folder, filling in the vault path.

Usage: python scripts/install_commands.py --vault "<vault path>" [--dest ~/.claude/commands]
Existing files are not overwritten unless --force is given.
"""
import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "commands"


def install(vault: str, dest: Path, force: bool = False) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    done = []
    for src in sorted(SRC.glob("*.md")):
        target = dest / src.name
        if target.exists() and not force:
            print(f"skip    {target} (exists; use --force)")
            continue
        target.write_text(src.read_text(encoding="utf-8").replace("{{VAULT}}", vault), encoding="utf-8")
        print(f"install {target}")
        done.append(src.name)
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--dest", type=Path, default=Path.home() / ".claude" / "commands")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    install(args.vault, args.dest, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
