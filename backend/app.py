from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import os
import json
from typing import Optional
import uuid
import asyncio

# dotenv & openai (optional)
from dotenv import load_dotenv
try:
    import openai
except Exception:
    openai = None

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = (BASE_DIR / ".." / "asiaspanel-web2").resolve()
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Load .env from repo root if present
load_dotenv(str(BASE_DIR.parent / '.env'))

# Configure OpenAI if key present
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY and openai is not None:
    openai.api_key = OPENAI_API_KEY

# Azure Storage connection string (optional). If set, we'll upload TTS to blob storage.
AZURE_CONN = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
_blob_service = None
if AZURE_CONN:
    try:
        from azure.storage.blob import BlobServiceClient
        _blob_service = BlobServiceClient.from_connection_string(AZURE_CONN)
    except Exception:
        _blob_service = None

app = FastAPI(title="Asia's Panel - Local Backend (FastAPI)")

# Allow local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: static files are mounted after API routes to avoid shadowing API endpoints.


class TranslateRequest(BaseModel):
    text: str
    source: Optional[str] = "auto"
    target: Optional[str] = "en"


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "default"
    format: Optional[str] = "wav"


@app.post("/api/translate")
async def translate(req: TranslateRequest):
    """Mock translation endpoint. If OPENAI_API_KEY is set, this is a stub that still returns a mock response
    so local testing doesn't require a live OpenAI key. Replace the body with a real OpenAI call later.
    """
    text = req.text or ""
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    # If OpenAI key is configured, call OpenAI to translate.
    # Support both old (module-level ChatCompletion) and new (openai.OpenAI client) interfaces.
    if OPENAI_API_KEY and openai is not None:
        model = os.getenv('OPENAI_MODEL', 'gpt-4')

        def call_openai():
            prompt = f"Translate the following text to {req.target}:\n\n{text}\n\nReturn only the translation."
            # Try the new openai.OpenAI client (openai>=1.0.0)
            try:
                if hasattr(openai, 'OpenAI'):
                    client = openai.OpenAI()
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                    )
                    # new client returns objects with .choices[0].message.content
                    try:
                        return resp.choices[0].message.content.strip()
                    except Exception:
                        # fallback to dict-like access
                        return resp['choices'][0]['message']['content'].strip()
            except Exception:
                # fall through to older API attempt
                pass

            # Fallback: older module-level ChatCompletion API (openai<1.0.0)
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp["choices"][0]["message"]["content"].strip()

        try:
            translated = await asyncio.to_thread(call_openai)
            return {"translated": translated, "target": req.target, "mock": False}
        except Exception as e:
            # Fall back to mock on error but return the error for debugging
            translated = text[::-1]
            return {"translated": translated, "target": req.target, "mock": True, "error": str(e)}

    # Simple mocked translation: return the text reversed and indicate the target language.
    translated = text[::-1]
    return {"translated": translated, "target": req.target, "mock": True}


@app.post("/api/tts")
async def tts(req: TTSRequest):
    """Mock TTS endpoint. Returns a small JSON pointer to where audio would be available.
    In production, this would call an external TTS provider and store the audio blob.
    """
    if not req.text:
        raise HTTPException(status_code=400, detail="text is required")

    # Create an MP3 filename for output
    audio_filename = f"tts_{uuid.uuid4().hex}.mp3"
    audio_path = STORAGE_DIR / audio_filename

    def _return_uploaded(path: Path):
        if _blob_service is not None:
            try:
                container_name = os.getenv('AZURE_TTS_CONTAINER', 'tts-audio')
                try:
                    _blob_service.create_container(container_name)
                except Exception:
                    pass
                blob_client = _blob_service.get_blob_client(container=container_name, blob=path.name)
                with open(path, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True)
                return {"url": blob_client.url, "mock": False, "storage": "azure"}
            except Exception as e:
                return {"url": f"/storage/{path.name}", "mock": False, "error": str(e)}
        return {"url": f"/storage/{path.name}", "mock": False}

    openai_error = None

    # Try OpenAI TTS if configured
    if OPENAI_API_KEY and openai is not None:
        try:
            audio_bytes = None
            # Newer client style: openai.OpenAI()
            if hasattr(openai, 'OpenAI'):
                try:
                    client = openai.OpenAI()
                    if hasattr(client, 'audio') and hasattr(client.audio, 'speech'):
                        model = os.getenv('OPENAI_TTS_MODEL', 'gpt-4o-mini-tts')
                        resp = client.audio.speech.create(model=model, voice=req.voice or 'alloy', input=req.text)
                        audio_bytes = resp
                except Exception:
                    audio_bytes = None

            # Fallback older module-level API
            if audio_bytes is None and hasattr(openai, 'audio'):
                try:
                    model = os.getenv('OPENAI_TTS_MODEL', 'gpt-4o-mini-tts')
                    resp = openai.audio.speech.create(model=model, voice=req.voice or 'alloy', input=req.text)
                    audio_bytes = resp
                except Exception:
                    audio_bytes = None

            # If we got bytes-like data or a file-like object, write to disk
            if audio_bytes is not None:
                if isinstance(audio_bytes, (bytes, bytearray)):
                    audio_path.write_bytes(audio_bytes)
                    return _return_uploaded(audio_path)
                else:
                    try:
                        data = audio_bytes.read()
                        if isinstance(data, (bytes, bytearray)):
                            audio_path.write_bytes(data)
                            return _return_uploaded(audio_path)
                    except Exception:
                        # Not file-like; continue to fallback
                        pass
        except Exception as e:
            openai_error = str(e)

    # Fallback to gTTS (local) for creating mp3 audio
    try:
        from gtts import gTTS
        tts = gTTS(text=req.text, lang=os.getenv('TTS_LANG', 'en'))
        tts.save(str(audio_path))
        result = _return_uploaded(audio_path)
        if openai_error:
            result['openai_error'] = openai_error
        return result
    except Exception as e:
        # Last resort: write a text placeholder and return local path
        placeholder_name = f"tts_{uuid.uuid4().hex}.txt"
        placeholder_path = STORAGE_DIR / placeholder_name
        placeholder_path.write_text(f"TTS fallback placeholder for voice={req.voice}, format={req.format}\n\n{req.text}")
        resp = {"url": f"/storage/{placeholder_path.name}", "mock": True, "error": str(e)}
        if openai_error:
            resp['openai_error'] = openai_error
        return resp


@app.get("/api/config")
async def get_config():
    cfg_file = STORAGE_DIR / "config.json"
    if not cfg_file.exists():
        return {"voices": ["default", "female_1", "male_1"], "settings": {}}
    return json.loads(cfg_file.read_text())
@app.post("/api/config")
async def save_config(payload: dict):

    cfg_file = STORAGE_DIR / "config.json"
    cfg_file.write_text(json.dumps(payload, indent=2))
    return {"ok": True}


# Serve storage files for demo purposes under /storage
if STORAGE_DIR.exists():
    app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")

# Mount the static frontend so a single server can serve both (mounted after API routes)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
