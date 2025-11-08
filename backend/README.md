# Asia's Panel — Local backend (FastAPI)

This folder contains a minimal FastAPI backend for local development. It is intentionally small and uses mocked responses so you can develop the frontend and wiring without requiring OpenAI keys.

Quick start (Windows cmd):

1. Create and activate your conda env (or use an existing one). This project uses `asia_02` by default.

Create it once (Anaconda Prompt / cmd):

```cmd
conda create -n asia_02 python=3.11 -y
conda activate asia_02
```

Or use the included helper script (from repo root) in an Anaconda Prompt:

```cmd
scripts\create_env.bat
```

Activate an existing env:

```cmd
conda activate asia_02
```

2. Install dependencies:

```cmd
pip install -r backend/requirements.txt
```

3. Run the app (serves frontend from `asiaspanel-web2`):

```cmd
uvicorn backend.app:app --reload --port 8001
```

4. Open http://localhost:8001 in your browser.

Endpoints:
- POST /api/translate  - body: {text, source?, target?}
- POST /api/tts        - body: {text, voice?, format?}
- GET /api/config
- POST /api/config

Notes:
- This is a local development scaffold. Replace mocked logic with real OpenAI calls when you have secure key handling in place.
- Storage is a local `backend/storage` folder. For Azure parity, use Azurite or Azure Blob Storage.
- For automation you can avoid activating the env and run using `conda run`. Example:

```cmd
& "C:\\Users\\%USERNAME%\\Miniconda3\\Scripts\\conda.exe" run -n asia_02 --no-capture-output uvicorn backend.app:app --reload --port 8001
```

OpenAI & Azurite (optional)
---------------------------
- To enable real translation using OpenAI, create a `.env` file at the repo root with:

```text
OPENAI_API_KEY=sk-REPLACE_WITH_YOUR_KEY
OPENAI_MODEL=gpt-4
```

- To enable blob storage for TTS (Azurite or real account), add a connection string to `.env`:

```text
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=...;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
```

- Start Azurite locally (optional) to emulate Azure Blob Storage:

```cmd
npm install -g azurite
azurite --silent --location .\azurite_storage --debug .\azurite_debug.log
```

Behavior summary:
- `/api/translate` will call OpenAI when `OPENAI_API_KEY` is present; otherwise falls back to the mocked response.
- `/api/tts` will attempt to call OpenAI TTS when `OPENAI_API_KEY` (and an appropriate `OPENAI_TTS_MODEL`) is present. If OpenAI TTS is not available or fails, the backend falls back to `gTTS` (local) to produce an MP3. The endpoint uploads the MP3 to blob storage if `AZURE_STORAGE_CONNECTION_STRING` is configured, otherwise serves it from `backend/storage`.

Security:
- Do NOT commit `.env` to git. Use `.env.example` as a template (provided).
- In CI use repository secrets (GitHub Actions secrets) and reference them in your workflow.
