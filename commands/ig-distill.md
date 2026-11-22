---
description: Turn raw Instagram captures into distilled notes
argument-hint: [folder name] [count, default 10]
---
Distill raw captures: $ARGUMENTS

The area is `{{VAULT}}/Instagram Brain`. Downloaded media and analysis are in `~/.insta-second-brain/cache/<shortcode>/`.

For each note with `status: raw` (filtered by the folder if one is given, at most the count asked for, default 10):

1. Read the caption, OCR text and transcript already in the note. For image posts, read at most 4 slide images from the cache folder. For reels, use the contact sheet in the cache `map*` folder only if the OCR text is not enough.
2. Fill in the summary callout, "What's shown", "What's said" and "Why it matters" following `docs/note-format.md`. Ignore transcripts that are only music. Do not invent content that is gated behind "comment a keyword"; write that it was not captured.
3. Rename the note to `Creator - Short Title.md`, add `[[wikilinks]]` to related notes, set `status: distilled`, and add `tags`.
4. Add one line to the hub index in `Instagram Brain.md` (newest first) and one line to `Log.md`.
5. Never delete a note. Do not overwrite an existing note with the new name without asking.
