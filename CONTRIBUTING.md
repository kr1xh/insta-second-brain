# insta-second-brain: contributor context

Goal: turn Instagram saved folders into an Obsidian vault second brain. See README for phases.

## Rules

- This repo is public. Never commit cookies, `sessions/`, `storage_state*.json`, downloaded media, or vault notes. They are gitignored; keep it that way.
- Tools (YoppaV/instagram-mcp, doughrun/instagram-scraper) are installed outside this repo. Document them, do not vendor them.
- Scripts must never modify or overwrite existing vault files. Support `--dry-run`.
- One issue per PR, branch `feat/<issue>-<slug>`, PR body includes `Closes #<n>`.
- Instagram access is read-only, slow, in small batches, with the user present for login.
