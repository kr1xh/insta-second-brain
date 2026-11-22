# Sweeping collections

`scripts/sweep.py` turns saved collections into raw notes in two stages, so the browser is never open while the heavy analysis runs.

| Stage | Touches Instagram | What it does |
|---|---|---|
| `collections` | yes, read-only | Lists collections. `--counts` adds the exact post count of each, read from the collections GraphQL response while the saved page loads (one page visit in total), and saves `collections.json` in the state directory. |
| `capture` | yes, read-only | Downloads posts of one collection, newest first, with a 12 to 25 s pause, and writes a raw note per post. Closes the browser when done. |
| `analyse` | no | For each captured video: on-screen text (OCR), transcript (Whisper), key-frame contact sheet. Fills in the note, then deletes the video and the frame scan. |

Run `capture` and `analyse` with the Python from the instagram-mcp virtualenv (for `instagram_sdk`).

```powershell
$py = "C:\path\to\ig-tools\instagram-mcp\venv\Scripts\python.exe"
$ig = "C:\path\to\ig-tools\instagram-scraper\plugins\instagram-scraper\skills\instagram-scraper\scripts\ig.py"
& $py scripts\sweep.py collections --handle YOURHANDLE --counts
& $py scripts\sweep.py capture --handle YOURHANDLE --collection "Cold email" `
  --vault "C:\path\to\vault" --map "$HOME\.insta-second-brain\folder-map.json" --limit 20
& $py scripts\sweep.py analyse --vault "C:\path\to\vault" --ig-py $ig
```

## Behaviour

- **Mapping.** `folder-map.json` maps each collection name to an area folder, for example `{"Cold email": "Internships and Research"}`. Keep it private. Collections not in the map go to `Inbox`.
- **Notes.** Each post becomes `Instagram Brain/<Area>/<creator> - <shortcode>.md` with `status: raw`. Existing notes are never overwritten.
- **Duplicates.** A post saved in more than one collection gets one note. The other collections are listed in `also_in:`. Notes are found by the shortcode in `source:`, so renamed (distilled) notes are still matched.
- **Resume.** Progress is saved after every post in `~/.insta-second-brain/sweep_state.json`. Already captured posts are skipped next time.
- **Auto-stop.** If Instagram redirects to a login, challenge or suspension page, the run stops immediately with exit code 4. Progress is kept. Do not retry that day; see [risk-controls.md](risk-controls.md).
- **Transcripts.** Whisper can invent speech from music. A transcript is kept only if speech was detected, the language is in `--langs` (default `en,hi`) and the language confidence is at least 0.8.
- **Disk.** After analysis only the contact sheets, OCR text, transcript and video map are kept (under 1 MB per post). Failed analyses keep the video for a retry.
- **Memory.** `--whisper-model` defaults to `small`. Use `base` on machines with little free RAM.
- **Speed.** On a 4-core laptop CPU, OCR is the slowest step (about 3.5 s per frame). `--ocr-every 10` (the default) OCRs once a second instead of doughrun's 5 times a second, through `scripts/ig_video.py`, without editing doughrun. Measured on a 10 s reel: OCR 72 s to 35 s, total 90 s to 73 s; the text lost was flickering numbers. `--ocr-every 0` restores doughrun's rate.

Known limits: comments are not read, so content gated behind "comment a keyword" is not captured. Image slides are saved but read only when a note is distilled.
