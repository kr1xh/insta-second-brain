---
description: Fill gated Instagram notes with sources found on the open web
argument-hint: [area or folder] [count, default 5]
---
Fill gaps in gated notes: $ARGUMENTS

The area is `{{VAULT}}/Instagram Brain`. Work on notes with `gated: true` and no `gap_filled:` field (filtered by area or folder if given, at most the count asked for, default 5).

For each note:
1. Find what the post names but hides: a paper title on screen, a repo or tool name, a lab, a programme, a dataset. If nothing specific is named, skip the note and add `gap_filled: false`.
2. Search the web for each named item. Prefer primary sources: the paper (arXiv, DOI), the official repo, the lab or programme page. Use secondary coverage only when no primary source turns up, and say so.
3. Add a `## Found elsewhere` section before `## Why it matters`:
   ```
   ## Found elsewhere
   > [!note] Found by web search on YYYY-MM-DD, not taken from the post.
   - What it is: URL. One line of what the source confirms.
   - Caveats the source raises (limits, deprecations, licence unknown).
   ```
4. Never present search results as what the creator said, and never guess at a gated template or DM'd link.
5. Add `gap_filled: true` to the frontmatter and append one line to `Log.md`.
