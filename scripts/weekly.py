"""Unattended capture runs: weekly (a fixed limit per collection) or daily (a total budget in priority order).

Usage: python scripts/weekly.py --config ~/.insta-second-brain/weekly.json

Config (keep it private, outside the repo):
  {"python": "<instagram-mcp venv python>", "handle": "...", "vault": "...", "map": "...",
   "ig_py": "<doughrun ig.py>", "collections": ["Cold email", "..."], "limit": 20}
Add "daily_total": 10 for daily mode: collections are filled in the listed order from their
remaining triage keeps, untriaged ones last, and "limit" is ignored.

Stops everything if Instagram shows a challenge or login page (exit code 4 from capture).
Output is appended to weekly.log next to the config.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sweep import safe_name  # noqa: E402  (same naming as the triage command)

SWEEP = Path(__file__).resolve().parent / "sweep.py"
BLOCKED = 4


KEEP_ROW = re.compile(r"^\| keep \| \[([^\]]+)\]", re.M)


def triage_table(vault: str | Path, name: str) -> Path:
    return Path(vault) / "Instagram Brain" / "Triage" / f"{safe_name(name)}.md"


def remaining_keeps(vault: str | Path, collections: list[str], state: dict) -> dict[str, int | None]:
    """Keep rows not captured yet, per collection; None when a collection has no triage table."""
    out: dict[str, int | None] = {}
    for name in collections:
        table = triage_table(vault, name)
        if not table.exists():
            out[name] = None
            continue
        keeps = set(KEEP_ROW.findall(table.read_text(encoding="utf-8")))
        out[name] = len(keeps - set(state.get(name, [])))
    return out


def capture_cmd(cfg: dict, name: str, limit: int) -> list[str]:
    cmd = [cfg["python"], str(SWEEP), "capture", "--handle", cfg["handle"], "--collection", name,
           "--vault", cfg["vault"], "--map", cfg["map"], "--limit", str(limit)]
    table = triage_table(cfg["vault"], name)
    if table.exists():
        cmd += ["--picks", str(table)]
    return cmd


def analyse_cmd(cfg: dict) -> list[str]:
    return [cfg["python"], str(SWEEP), "analyse", "--vault", cfg["vault"], "--ig-py", cfg["ig_py"]]


def plan(cfg: dict) -> list[list[str]]:
    """Weekly mode: one capture per collection with the same limit, then one analyse."""
    steps = [capture_cmd(cfg, name, int(cfg.get("limit", 20))) for name in cfg["collections"]]
    steps.append(analyse_cmd(cfg))
    return steps


def run_daily(cfg: dict, runner, load_state) -> int:
    """Daily mode: spend `daily_total` captures on collections in priority order (untriaged ones last).

    The budget is charged with what each capture actually added to sweep state, so a folder whose
    remaining keeps can never be captured (deleted, unsaved, always timing out) passes its share on.
    """
    budget = int(cfg["daily_total"])
    order = cfg["collections"]
    first = remaining_keeps(cfg["vault"], order, load_state())
    queue = [n for n in order if first[n]] + [n for n in order if first[n] is None]
    for name in queue:
        if budget <= 0:
            break
        left = remaining_keeps(cfg["vault"], [name], load_state())[name]
        if left == 0:
            continue
        take = budget if left is None else min(left, budget)
        before = len(load_state().get(name, []))
        if runner(capture_cmd(cfg, name, take)) == BLOCKED:
            return BLOCKED
        budget -= max(0, len(load_state().get(name, [])) - before)
    return runner(analyse_cmd(cfg))


def no_window_flags() -> int:
    """On Windows, start steps without a console window, so closing a window cannot kill the run."""
    return 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW


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
            return subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, creationflags=no_window_flags(),
                                  env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode

    state_path = Path(cfg.get("state", args.config.with_name("sweep_state.json")))

    def load_state() -> dict:
        return json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    code = run_daily(cfg, runner, load_state) if cfg.get("daily_total") else run(cfg, runner)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"== finished with exit code {code}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
