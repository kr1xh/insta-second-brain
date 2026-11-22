# Note format

One note per saved post or reel, in `Instagram Brain/<Area>/`, named `Creator - Short Title.md`. Raw captures from the sweep are named `creator - shortcode.md` until they are distilled and renamed.

## Frontmatter

```yaml
type: saved-post
source: https://www.instagram.com/<creator>/reel/<shortcode>/
creator: "@creator"
folder: Cold email          # the original Instagram collection name
kind: reel                  # post | reel
captured: 2026-11-22
status: raw                 # raw | distilled
tags: []
```

`folder` always keeps the Instagram collection, even though the note lives in a grouped area. That keeps the mapping reversible.

## Sections, in order

1. **Summary callout**: one line on what it is and why it was saved.
2. **What's shown**: on-screen text and visuals. For reels, from OCR and key frames; for carousels, one line per slide.
3. **What's said**: the useful part of the transcript. Ignore it when the audio is only music; Whisper can hallucinate speech from music.
4. **Caption and comments**: the caption, hashtags and any comment that carries content. Say so when the real content is gated behind "comment a keyword".
5. **Why it matters**: how it connects to your goals.
6. **Related**: `[[wikilinks]]` to other notes and to `[[Instagram Brain]]`.

## Status

- `raw`: written by the sweep. Caption, OCR text and transcript only. Image slides are saved but not read.
- `distilled`: someone read the material and filled in the summary and "Why it matters".

## Rules

- Separate what the post says from your own inference.
- Do not copy a gated template you never saw; mark it as not captured.
- Never delete a note. If unsure where it belongs, move it to `Inbox/`.
- Do not overwrite an existing note without asking.
