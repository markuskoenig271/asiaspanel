# Runbook — Local development: uvicorn backend and frontend

This runbook collects practical steps and commands to run, stop, restart, and troubleshoot the local development server used by "Asia's Panel" (FastAPI backend served with uvicorn, static frontend in `asiaspanel-web2`). It also documents common issues (OpenAI client migration, TTS fallback, Azurite), quick verification commands, and where to look for logs.

## Goals
- Start the backend and static frontend on your machine so you can demo the UI at http://127.0.0.1:8002
- Stop/restart the backend cleanly
- Troubleshoot common problems (port-in-use, OpenAI migration errors, missing TTS dependency)
- Provide quick curl examples to test endpoints

## Files referenced
- `backend/app.py` — FastAPI application and API endpoints (`/api/translate`, `/api/tts`, `/api/config`).
- `asiaspanel-web2/index.html` — static frontend wired to the backend endpoints.
- `scripts/run_local.bat` — helper to start the server in the `asia_02` conda env.
- `scripts/stop_local.bat` — helper to stop any process listening on ports 8002 / 8004.
- `backend/storage/` — local storage used for generated TTS files and `config.json` in dev.
- `.env` (local; not in git) — place your `OPENAI_API_KEY` and optional `AZURE_STORAGE_CONNECTION_STRING` here.

## Requirements
- Windows (commands shown for cmd.exe and PowerShell)
- A conda environment named `asia_02` created with `scripts/create_env.bat` (or create manually)
- Python packages installed from `backend/requirements.txt` (the env helper installs them when you run it)

## Quick start (recommended)
1. Open a cmd window in the repository root.
2. Start the server with the helper (recommended):

```cmd
scripts\run_local.bat
```

This helper runs uvicorn using your `asia_02` conda environment and serves the static frontend and API on port 8002 by default.

3. Open the browser to:

- http://127.0.0.1:8002/ or http://localhost:8002/

## Manual start (if you prefer)
Use the `python.exe` from the conda environment to avoid `conda run` quoting issues.

CMD:
```cmd
"%USERPROFILE%\Miniconda3\envs\asia_02\python.exe" -m uvicorn backend.app:app --port 8002 --host 127.0.0.1
```
PowerShell (explicit):
```powershell
& "$env:USERPROFILE\Miniconda3\envs\asia_02\python.exe" -m uvicorn backend.app:app --port 8002 --host 127.0.0.1
```

If you use Anaconda instead of Miniconda, replace `Miniconda3` with `Anaconda3` in the path.

### Start on an alternate port (no need to kill existing processes)
```cmd
"%USERPROFILE%\Miniconda3\envs\asia_02\python.exe" -m uvicorn backend.app:app --port 8004 --host 127.0.0.1
```

## Stop the server (recommended)
- If uvicorn was started in a terminal you control, switch to that terminal and press Ctrl+C — this is the cleanest shutdown.
- If the process is detached or started from the helper, use the provided stop script:

```cmd
scripts\stop_local.bat
```

`stop_local.bat` finds a process listening on port 8002 or 8004 and calls `taskkill /PID <pid> /F`.

Manual stop using Windows tools:
1. Find the process listening on 8002:
```cmd
netstat -ano | findstr ":8002"
```
2. Kill the PID (replace 32456 with the PID you found):
```cmd
taskkill /PID 32456 /F
```

## Restart workflow
1. Stop the running server (Ctrl+C or `scripts\stop_local.bat`).
2. Start the server (helper or manual command above).
3. Verify the root page: open http://127.0.0.1:8002/ in your browser or run `curl` (see below).

## Quick verification & tests
- Check page is served (curl):
```cmd
curl.exe -v http://127.0.0.1:8002/
```
- Translate API (POST):
```cmd
curl.exe -X POST "http://127.0.0.1:8002/api/translate" -H "Content-Type: application/json" -d "{\"text\":\"Hello world\",\"target\":\"de\"}"
```
- TTS API (POST):
```cmd
curl.exe -X POST "http://127.0.0.1:8002/api/tts" -H "Content-Type: application/json" -d "{\"text\":\"Hello from Asia's Panel\",\"voice\":\"default\"}"
```
Look for `{"url":"/storage/tts_...mp3"}` and open that URL in the browser to play the audio.

## Common problems and fixes

### 1) Port in use / uvicorn fails to bind
- Symptom: uvicorn logs show `error while attempting to bind on address ('0.0.0.0', 8002): normally each socket address ... only once` or you cannot access the page.
- Fix: find the listening PID and stop it; or start on a different port (8004). Use `scripts\stop_local.bat` or `taskkill`.

### 2) OpenAI client error (migration message)
- Symptom: translate returns an error like:
  "You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0 ..."
- Cause: installed `openai` is >=1.0.0 but the code used the old module-level ChatCompletion API.
- Fix (recommended): keep the `openai` package up-to-date and use the new client API; `backend/app.py` has been updated to support both the new `openai.OpenAI()` client and fallback to older module-level calls. No action needed unless you prefer to pin.
- Alternative (pin the old behavior):
```cmd
conda run -n asia_02 --no-capture-output pip install openai==0.28
```

### 3) gTTS import or TTS generation error
- Symptom: `/api/tts` returns an error about gtts import or fails to produce mp3.
- Fix: ensure `gtts` is installed in `asia_02` (the helper installs this). Check `backend/requirements.txt` and `pip install gTTS` in that env. If network is required for gTTS, the fallback placeholder will be generated.

### 4) Static frontend not served / wrong path
- Symptom: visiting root shows a 404 or incorrect content.
- Fix: `backend/app.py` mounts `asiaspanel-web2` as the static root when it exists. Ensure `asiaspanel-web2/index.html` exists and that uvicorn was started from the repository root (start uvicorn with the working directory set to the repo root).

## TTS API migration and behavior notes
- The app attempts TTS in this order:
  1. If `OPENAI_API_KEY` exists and a modern OpenAI client is available, it tries the new OpenAI TTS path (supports `openai.OpenAI()` client shape where available).
  2. If that fails, or if OpenAI TTS isn't available, it falls back to `gTTS` (local) to synthesize MP3.
  3. If `gTTS` fails (for any reason), a text placeholder file is written to `backend/storage` and the endpoint returns a URL to that placeholder.
- You can configure `OPENAI_TTS_MODEL` and `AZURE_TTS_CONTAINER` via `.env`.

## Azurite / Azure Blob (optional)
- If you want to exercise Azure Blob upload locally, run Azurite (Docker or npm) and set `AZURE_STORAGE_CONNECTION_STRING` in `.env`. The backend will upload generated audio to the configured container and return the blob URL.
- Azurite quick start (Docker):
```bash
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite
```
- Then configure `.env` with the connection string Azurite exposes (or use the emulator default in docs).

## Logs
- When running uvicorn in the foreground, logs appear in the terminal where you started the server.
- If you start uvicorn detached or via a helper that opens a new window, use Task Manager or `netstat` to find the PID and inspect logs where you redirected them (if you enabled redirection in your start command). You can also temporarily start without detaching to watch logs.

## Development tips
- Using `--reload` is convenient for code changes, but it spawns a reloader process which can complicate PID-based stop logic; Ctrl+C in that terminal still stops the server cleanly.
- If you prefer one persistent process, start uvicorn without `--reload` and use your editor's watch/test loop to restart manually after changes.

## Useful commands summary
- Start (helper): `scripts\run_local.bat`
- Stop (helper): `scripts\stop_local.bat`
- Manual start (cmd):
  - `"%USERPROFILE%\\Miniconda3\\envs\\asia_02\\python.exe" -m uvicorn backend.app:app --port 8002 --host 127.0.0.1`
- Check root page: `curl.exe -v http://127.0.0.1:8002/`
- Translate test: `curl.exe -X POST "http://127.0.0.1:8002/api/translate" -H "Content-Type: application/json" -d "{\"text\":\"Hello world\",\"target\":\"de\"}"`
- Find listener (netstat): `netstat -ano | findstr ":8002"`
- Kill PID: `taskkill /PID <pid> /F`

## Next steps / suggestions
- If you frequently demo this app, consider adding `scripts\start_local.bat` that launches uvicorn in a visible window and `scripts\stop_local.bat` which we added already.
- Add a small `/health` endpoint (JSON) to `backend/app.py` so monitoring scripts can quickly verify readiness.
- Document how to set `OPENAI_API_KEY` into `.env` for demos requiring real translation/TTS from OpenAI.

---

If you'd like, I can also:
- Add a `scripts/start_local.bat` pair to complement the stop script (one-click start/stop),
- Add a `/health` endpoint to `backend/app.py`, or
- Add a short `README_DEMO.md` with step-by-step demo instructions you can follow when showing the app to someone.

Which of those would you like next?
