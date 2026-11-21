# Windows setup

Tested on Windows 11. Two read-only tools do the Instagram side. Both install outside this repo (here: `C:\Users\<you>\Downloads\GITHUB\ig-tools\`).

| Tool | Job | Audited commit |
|---|---|---|
| [YoppaV/instagram-mcp](https://github.com/YoppaV/instagram-mcp) | Lists saved collections and post URLs | `47fb2a6` |
| [doughrun/instagram-scraper](https://github.com/doughrun/instagram-scraper) | Per-post analysis: caption, comments, scene map, OCR, transcript | `3a94a3d` |

Both repos are young and have almost no stars. Their source was read before use: they only contact instagram.com and Instagram's media hosts, and they do not send data anywhere else. Pin to those commits and re-read the diff before pulling updates.

## 1. Prerequisites

```powershell
winget install --id=Gyan.FFmpeg -e
winget install --id=astral-sh.uv -e
```

Open a new terminal afterwards. Check with `ffmpeg -version` and `uv --version`.

## 2. Windows Defender Controlled Folder Access

If your vault is in `Documents` or `Desktop`, Controlled Folder Access blocks scripts from writing there, and the error looks like "file not found". Allow only Python, from an administrator PowerShell:

```powershell
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\Python311\python.exe"
```

## 3. YoppaV/instagram-mcp

```powershell
cd ig-tools
git clone https://github.com/YoppaV/instagram-mcp.git
cd instagram-mcp
git checkout 47fb2a6
uv venv venv --python 3.12
uv pip install --python venv -r requirements.txt
uv pip install --python venv -e .
venv\Scripts\python -m playwright install chromium
venv\Scripts\python -m unittest discover tests     # offline, should pass
claude mcp add instagram --scope user -- "$PWD\venv\Scripts\instagram-mcp.exe"
```

Its login session is stored in `~/.instagram-mcp/sessions/`. That folder is private; never copy it into a repo or vault.

## 4. doughrun/instagram-scraper

Install from the local clone so the code you audited is the code that runs:

```powershell
cd ig-tools
git clone https://github.com/doughrun/instagram-scraper.git
cd instagram-scraper
git checkout 3a94a3d
claude plugin marketplace add "$PWD"
claude plugin install instagram-scraper@instagram-scraper
```

Its first-run setup edits your Claude Code `settings.json` to add permission rules. Review that change using the checklist in [risk-controls.md](risk-controls.md).

## 5. Logging in

Log in yourself, in the browser window each tool opens. Never type your password into a chat or a file.

```powershell
cd ig-tools\instagram-mcp
venv\Scripts\python -m scripts.auth_login --username <handle>
```

Use a secondary Instagram account if you can (see [risk-controls.md](risk-controls.md)).

## 6. Verify

```powershell
claude mcp list          # instagram should show Connected
claude plugin list       # instagram-scraper should show enabled
```
