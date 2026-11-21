"""Fail if private data (cookies, sessions, media, vault notes) is about to be committed.

Usage:
  python scripts/check_no_secrets.py          # check staged files
  python scripts/check_no_secrets.py --all    # check every tracked file (CI)
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FORBIDDEN_PATHS = [
    (re.compile(r"(^|/)sessions/"), "login session directory"),
    (re.compile(r"storage_state[^/]*\.json$"), "browser storage state"),
    (re.compile(r"_instagram_state\.json$"), "Instagram session state"),
    (re.compile(r"(^|/)cookies?[^/]*\.(json|txt)$", re.I), "cookie file"),
    (re.compile(r"(^|/)\.env(\.(?!example$)[^/]*)?$"), "env file"),
    (re.compile(r"\.(mp4|mov|mkv|webm|wav|mp3)$", re.I), "media file"),
    (re.compile(r"(^|/)8 - Instagram Second Brain/"), "vault notes"),
    (re.compile(r"(^|/)(downloads|media|inbox|notes)/"), "downloaded or captured data"),
]

FORBIDDEN_CONTENT = [
    (re.compile(r"sessionid[\"'=:\s]+[A-Za-z0-9%]{20,}", re.I), "Instagram sessionid value"),
    (re.compile(r"ds_user_id[\"'=:\s]+\d{5,}", re.I), "Instagram ds_user_id value"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
]

SELF_EXEMPT = {"scripts/check_no_secrets.py", "tests/test_check_no_secrets.py"}


def files(all_files: bool) -> list[str]:
    cmd = ["git", "ls-files"] if all_files else ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    out = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def check(paths: list[str], read=lambda p: (REPO / p).read_bytes()) -> list[str]:
    problems = []
    for p in paths:
        for rx, why in FORBIDDEN_PATHS:
            if rx.search(p):
                problems.append(f"{p}: {why}")
        if p in SELF_EXEMPT:
            continue
        try:
            text = read(p).decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for rx, why in FORBIDDEN_CONTENT:
            if rx.search(text):
                problems.append(f"{p}: contains {why}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="check all tracked files")
    args = ap.parse_args(argv)
    problems = check(files(args.all))
    if problems:
        print("Private data must not be committed:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("ok: no private data found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
