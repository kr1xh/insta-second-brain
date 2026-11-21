# insta-second-brain

Turn your saved Instagram folders into a searchable second brain in Obsidian, including what is shown and said inside each reel.

> Status: early. Built in phases (see Milestones). Nothing here scrapes anything yet.

## What it does (target)

1. Lists your Instagram saved collections.
2. Analyzes each post or reel locally: caption, comments, on-screen text (OCR), transcript (Whisper), key frames.
3. Writes one Markdown note per post into an Obsidian vault, grouped like your Instagram folders, with frontmatter, wikilinks and an index.
4. Lets an AI assistant query the vault and draft emails, project plans and reel scripts from it.

## Privacy

This repo holds code, templates, docs and slash commands only. Your notes, login sessions, cookies and downloaded media live in your private vault and are gitignored. A guard script (planned) fails CI if anything private is staged.

## Phases

| Milestone | Goal |
|---|---|
| M0 | Repo, vault scaffold, secret guard |
| M1 | Tool setup on Windows, risk controls, manual login |
| M2 | Pilot on one small folder |
| M3 | Full sweep with batching and resume |
| M4 | `/query`, `/draft`, vault health, cleanup |

## Risk

Reading a logged-in Instagram account with third-party tools can get the account flagged. See `docs/risk-controls.md` (coming in M1). Use at your own risk, on your own account.

## License

MIT
