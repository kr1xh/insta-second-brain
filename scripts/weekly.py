"""Weekly unattended run: capture new saves from a few collections, then analyse them.

Usage: python scripts/weekly.py --config ~/.insta-second-brain/weekly.json

Config (keep it private, outside the repo):
  {"python": "<instagram-mcp venv python>", "handle": "...", "vault": "...", "map": "...",
   "ig_py": "<doughrun ig.py>", "collections": ["Cold email", "..."], "limit": 20}

Stops everything if Instagram shows a challenge or login page (exit code 4 from capture).
Output is appended to weekly.log next to the config.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sweep import safe_name  # noqa: E402  (same naming as the triage command)

SWEEP = Path(__file__).resolve().parent / "sweep.py"
BLOCKED = 4


def plan(cfg: dict) -> list[list[str]]:
    """One capture per collection (using its triage table when there is one), then one analyse."""
    triage_dir = Path(cfg["vault"]) / "Instagram Brain" / "Triage"
    steps = []
    for name in cfg["collections"]:
        cmd = [cfg["python"], str(SWEEP), "capture", "--handle", cfg["handle"], "--collection", name,
               "--vault", cfg["vault"], "--map", cfg["map"], "--limit", str(cfg.get("limit", 20))]
        table = triage_dir / f"{safe_name(name)}.md"
        if table.exists():
            cmd += ["--picks", str(table)]
        steps.append(cmd)
    steps.append([cfg["python"], str(SWEEP), "analyse", "--vault", cfg["vault"], "--ig-py", cfg["ig_py"]])
    return steps


def run(cfg: dict, runner) -> int:
    steps = plan(cfg)
    for cmd in steps[:-1]:
        if runner(cmd) == BLOCKED:
            return BLOCKED
    return runner(steps[-1])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    args = ap.parse_args(argv)
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    log = args.config.with_name("weekly.log")

    def runner(cmd: list[str]) -> int:
        with log.open("a", encoding="utf-8") as fh:
            step = " ".join(cmd[2:5])
            fh.write(f"\n== {datetime.now():%Y-%m-%d %H:%M} {step}\n")
            fh.flush()
            return subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                                  env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode

    code = run(cfg, runner)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"== finished with exit code {code}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
