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

- **Creator comments.** Many creators put the template or link "in the comments". The post page embeds its comments as JSON, so `capture` adds the creator's own comments to the note at no extra request. For notes captured earlier, `comments --vault <vault> --limit N` revisits gated notes (or captions that mention comments), paced, and adds them; each note is marked `comments_checked: true` so it is visited once. Notes still waiting for `analyse` are skipped.

Known limits: other people's comments are not read, and content sent by DM ("comment EMAIL and I'll send it") cannot be captured. Image slides are saved but read only when a note is distilled.

## Scheduled runs

`scripts/weekly.py --config <config>` runs capture and then `analyse` without you. It has two modes:

- **Daily** (`"daily_total": 10` in the config): captures 10 posts in total per run, filling the listed collections in order from their remaining triage keeps (untriaged collections last). A collection whose keeps cannot be captured passes its share to the next one.
- **Weekly** (no `daily_total`): captures up to `limit` posts from each listed collection.

Both stop everything if a capture exits with code 4 (Instagram challenge or login page) and append all output to `weekly.log` next to the config. Keep the config private; see the docstring in `scripts/weekly.py` for its fields.

Create the task once. Use `pythonw.exe` so no console window opens (closing one would kill the run). The task needs you logged in, and the laptop must stay awake: a closed lid or sleep pauses the run until it wakes.

```powershell
schtasks /Create /TN "insta-second-brain daily" /SC DAILY /ST 21:00 `
  /TR "\"C:\path\to\venv\Scripts\pythonw.exe\" \"C:\path\to\insta-second-brain\scripts\weekly.py\" --config \"%USERPROFILE%\.insta-second-brain\daily.json\""
```

Any task named `insta-second-brain <name>` can then be controlled with `scripts/ig-scrape.ps1`:

```powershell
$ig = "C:\path\to\insta-second-brain\scripts\ig-scrape.ps1"
powershell -ExecutionPolicy Bypass -File $ig status                     # on/off, times, next run
powershell -ExecutionPolicy Bypass -File $ig run daily                  # run now, even while the schedule is off
powershell -ExecutionPolicy Bypass -File $ig stop                       # stop a run; captured posts are kept
powershell -ExecutionPolicy Bypass -File $ig off                        # pause all schedules ("unschedule" works too)
powershell -ExecutionPolicy Bypass -File $ig on daily                   # resume, with the same times
powershell -ExecutionPolicy Bypass -File $ig schedule daily 08:30 21:00 # new daily time(s)
```

The cap counts per run: `run` on top of the scheduled run, or two scheduled times, captures twice as many posts that day. To type just `ig-scrape`, put a one-line `ig-scrape.cmd` in a folder on your `PATH`:

```bat
@powershell -NoProfile -ExecutionPolicy Bypass -File "C:\path\to\insta-second-brain\scripts\ig-scrape.ps1" %*
```

Delete a task with `schtasks /Delete /TN "insta-second-brain daily" /F`.
