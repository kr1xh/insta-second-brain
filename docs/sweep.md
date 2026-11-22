# Sweeping a collection

`scripts/sweep.py` captures one saved collection into raw notes. It needs the Python from the instagram-mcp virtualenv (for `instagram_sdk`) and the logged-in session from [setup-windows.md](setup-windows.md).

```powershell
$py = "C:\path\to\ig-tools\instagram-mcp\venv\Scripts\python.exe"
& $py scripts\sweep.py collections --handle YOURHANDLE
& $py scripts\sweep.py run --handle YOURHANDLE --collection "Cold email" `
  --vault "C:\path\to\vault" --map "$HOME\.insta-second-brain\folder-map.json" `
  --ig-py "C:\path\to\ig-tools\instagram-scraper\plugins\instagram-scraper\skills\instagram-scraper\scripts\ig.py" `
  --limit 20
```

- `folder-map.json` maps each collection name to an area folder, for example `{"Cold email": "Internships and Research"}`. Keep it private; collections not in the map go to `Inbox`.
- Each post becomes `Instagram Brain/<Area>/<creator> - <shortcode>.md` with `status: raw`: caption, on-screen text (OCR) and transcript. Existing notes are never overwritten.
- Posts are fetched one at a time with a 12 to 25 second pause (`--pause-min`, `--pause-max`). Run batches of 20 to 30 and wait between them; see [risk-controls.md](risk-controls.md).
- Resume state and downloaded media live in `~/.insta-second-brain/` (`--state-dir`), never in the repo or vault. Already captured posts are skipped on the next run.
- Raw notes are distilled into summaries in a separate pass. Image slides are saved but not read until then.

Known limits: comments are not read, so content gated behind "comment a keyword" is not captured. Whisper can mistake music for speech; check the transcript before trusting it.
