from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
import io
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import os
import json
from typing import Optional
import uuid
import asyncio
import time
import logging
import requests
import secrets

# Configure logging to both console and file
# For Azure: only log to console (Azure captures stdout)
# For local: log to file if logs directory exists
LOGS_DIR = Path(__file__).resolve().parent.parent / 'logs'
log_handlers = [logging.StreamHandler()]  # Always log to console

# Only add file handler if we can create the logs directory (local development)
try:
    if LOGS_DIR.exists() or LOGS_DIR.parent.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / 'log_file.log'
        log_handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        print(f"File logging enabled: {log_file}")
except Exception as e:
    print(f"File logging disabled (running on Azure?): {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)
if len(log_handlers) > 1:
    logger.info(f"Logging to file: {log_file}")
else:
    logger.info("Logging to console only (Azure mode)")

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
VOICES_DIR = STORAGE_DIR / "voices"
VOICES_DIR.mkdir(parents=True, exist_ok=True)

# server start time for /health
START_TIME = time.time()

# Load .env from repo root if present
load_dotenv(str(BASE_DIR.parent / '.env'))

# Configure OpenAI if key present
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY and openai is not None:
    openai.api_key = OPENAI_API_KEY

# ElevenLabs API key for voice cloning
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Load master password from .pw file
PW_FILE = BASE_DIR / '.pw'
MASTER_PASSWORD = None
VALID_TOKENS = set()  # In-memory token storage

if PW_FILE.exists():
    MASTER_PASSWORD = PW_FILE.read_text().strip()
    logger.info(f"Authentication enabled - password loaded from {PW_FILE}")
else:
    logger.warning("No .pw file found - authentication disabled!")

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

# Authentication dependency
async def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify authentication token. Skip if no master password is set."""
    if not MASTER_PASSWORD:
        return True  # Auth disabled
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    if token not in VALID_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return True

# Note: static files are mounted after API routes to avoid shadowing API endpoints.


class AuthRequest(BaseModel):
    password: str


class TranslateRequest(BaseModel):
    text: str
    source: Optional[str] = "auto"
    target: Optional[str] = "en"


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "default"
    format: Optional[str] = "wav"


# ============ Authentication Endpoints (No Auth Required) ============

@app.post("/api/auth/login")
async def login(req: AuthRequest):
    """Login with master password and receive session token."""
    if not MASTER_PASSWORD:
        raise HTTPException(status_code=500, detail="Authentication not configured")
    
    if req.password != MASTER_PASSWORD:
        logger.warning("Failed login attempt")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    VALID_TOKENS.add(token)
    
    logger.info(f"Successful login - Active sessions: {len(VALID_TOKENS)}")
    return {"token": token, "message": "Login successful"}


@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout and invalidate token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        VALID_TOKENS.discard(token)
        logger.info(f"User logged out - Active sessions: {len(VALID_TOKENS)}")
    
    return {"message": "Logged out successfully"}


# ============ Protected API Endpoints ============

@app.post("/api/translate", dependencies=[Depends(verify_auth)])
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


@app.post("/api/tts", dependencies=[Depends(verify_auth)])
async def tts(req: TTSRequest):
    """TTS endpoint. Generates audio using OpenAI TTS or gTTS fallback.
    Uploads to Azure Blob Storage if configured, otherwise serves locally.
    """
    logger.info(f"TTS request: text='{req.text[:50]}...', voice={req.voice}, format={req.format}")
    
    if not req.text:
        logger.error("TTS request missing text")
        raise HTTPException(status_code=400, detail="text is required")

    # Create an MP3 filename for output
    audio_filename = f"tts_{uuid.uuid4().hex}.mp3"
    audio_path = STORAGE_DIR / audio_filename
    logger.info(f"Audio will be saved to: {audio_path}")

    def _return_uploaded(path: Path):
        logger.info(f"Attempting to upload/return audio: {path.name}")
        
        # Determine the base URL for audio endpoints
        # In production (Azure), use absolute URL; locally use relative URL
        backend_url = os.getenv('BACKEND_URL', '')
        
        if _blob_service is not None:
            try:
                container_name = os.getenv('AZURE_TTS_CONTAINER', 'tts-audio')
                logger.info(f"Uploading to Azure blob container: {container_name}")
                try:
                    _blob_service.create_container(container_name)
                    logger.info(f"Container {container_name} created or already exists")
                except Exception as ce:
                    logger.info(f"Container creation skipped: {ce}")
                    pass
                blob_client = _blob_service.get_blob_client(container=container_name, blob=path.name)
                with open(path, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True)
                proxied = f"{backend_url}/api/audio/{path.name}"
                logger.info(f"Audio uploaded to Azure, returning proxied URL: {proxied}")
                return {"url": proxied, "mock": False, "storage": "azure", "blob_url": blob_client.url}
            except Exception as e:
                logger.error(f"Azure blob upload failed: {e}", exc_info=True)
                return {"url": f"{backend_url}/storage/{path.name}", "mock": False, "error": str(e)}
        logger.info(f"No Azure blob configured, returning local storage URL")
        return {"url": f"{backend_url}/storage/{path.name}", "mock": False}
    
    openai_error = None

    # Check if this is a cloned voice (ElevenLabs)
    config_file = STORAGE_DIR / "config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        cloned_voices = config.get("cloned_voices", {})
        
        if req.voice in cloned_voices:
            # Use ElevenLabs for cloned voices
            elevenlabs_id = cloned_voices[req.voice]["elevenlabs_id"]
            logger.info(f"Using ElevenLabs cloned voice: {req.voice} ({elevenlabs_id})")
            
            if ELEVENLABS_API_KEY:
                try:
                    headers = {"xi-api-key": ELEVENLABS_API_KEY}
                    data = {
                        "text": req.text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,           # 0-1: Lower = more expressive/variable, Higher = more stable/consistent
                            "similarity_boost": 0.85,   # 0-1: Higher = closer to your voice sample (try 0.75-0.95)
                            "style": 0.0,               # 0-1: Speaker style strength (0 = neutral)
                            "use_speaker_boost": True   # Enhances similarity to original voice
                        }
                    }
                    
                    response = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{elevenlabs_id}",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    audio_path.write_bytes(response.content)
                    logger.info(f"ElevenLabs TTS successful for {audio_filename}")
                    return _return_uploaded(audio_path)
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"ElevenLabs TTS failed: {e}, falling back to OpenAI")
                    openai_error = f"ElevenLabs: {str(e)}"
                    # Fall through to OpenAI/gTTS
            else:
                logger.warning("ElevenLabs API key not configured for cloned voice")
                openai_error = "ElevenLabs API key not configured"

    # Try OpenAI TTS if configured
    if OPENAI_API_KEY and openai is not None:
        logger.info("Attempting OpenAI TTS generation")
        try:
            audio_bytes = None
            # Newer client style: openai.OpenAI()
            if hasattr(openai, 'OpenAI'):
                try:
                    client = openai.OpenAI()
                    if hasattr(client, 'audio') and hasattr(client.audio, 'speech'):
                        model = os.getenv('OPENAI_TTS_MODEL', 'tts-1')
                        logger.info(f"Using OpenAI TTS model: {model}, voice: {req.voice or 'alloy'}")
                        resp = client.audio.speech.create(model=model, voice=req.voice or 'alloy', input=req.text)
                        audio_bytes = resp
                        logger.info("OpenAI TTS response received")
                except Exception as e:
                    logger.warning(f"OpenAI new client TTS failed: {e}")
                    audio_bytes = None

            # If we got bytes-like data or a file-like object, write to disk
            if audio_bytes is not None:
                logger.info(f"Processing OpenAI audio bytes, type: {type(audio_bytes)}")
                if isinstance(audio_bytes, (bytes, bytearray)):
                    audio_path.write_bytes(audio_bytes)
                    logger.info(f"OpenAI audio written to {audio_path}")
                    return _return_uploaded(audio_path)
                else:
                    try:
                        data = audio_bytes.read()
                        if isinstance(data, (bytes, bytearray)):
                            audio_path.write_bytes(data)
                            logger.info(f"OpenAI audio (from stream) written to {audio_path}")
                            return _return_uploaded(audio_path)
                    except Exception as read_err:
                        logger.warning(f"Could not read OpenAI audio bytes: {read_err}")
                        pass
        except Exception as e:
            openai_error = str(e)
            logger.error(f"OpenAI TTS error: {openai_error}", exc_info=True)
    else:
        logger.info("OpenAI not configured or not available, skipping OpenAI TTS")

    # Fallback to gTTS (local) for creating mp3 audio
    logger.info("Attempting gTTS fallback")
    try:
        from gtts import gTTS
        tts_obj = gTTS(text=req.text, lang=os.getenv('TTS_LANG', 'en'))
        tts_obj.save(str(audio_path))
        logger.info(f"gTTS audio saved to {audio_path}")
        result = _return_uploaded(audio_path)
        if openai_error:
            result['openai_error'] = openai_error
        logger.info(f"Returning gTTS result: {result}")
        return result
    except Exception as e:
        logger.error(f"gTTS fallback failed: {e}", exc_info=True)
        # Last resort: write a text placeholder and return local path
        placeholder_name = f"tts_{uuid.uuid4().hex}.txt"
        placeholder_path = STORAGE_DIR / placeholder_name
        placeholder_path.write_text(f"TTS fallback placeholder for voice={req.voice}, format={req.format}\n\n{req.text}")
        resp = {"url": f"/storage/{placeholder_path.name}", "mock": True, "error": str(e)}
        if openai_error:
            resp['openai_error'] = openai_error
        logger.warning(f"Returning placeholder response: {resp}")
        return resp


@app.get('/api/audio/{name}')
async def audio_proxy(name: str):
    """Proxy and stream audio blobs from Azure (or serve local files) with proper CORS headers."""
    logger.info(f"Audio proxy request for: {name}")
    
    # First try Azure blob with connection string authentication
    if _blob_service is not None:
        try:
            container_name = os.getenv('AZURE_TTS_CONTAINER', 'tts-audio')
            logger.info(f"Fetching from Azure blob: {container_name}/{name}")
            
            blob_client = _blob_service.get_blob_client(container=container_name, blob=name)
            
            # Check if blob exists first
            if not blob_client.exists():
                logger.warning(f"Blob {name} does not exist in container {container_name}")
                # Don't raise yet, try local fallback
            else:
                # Download and stream
                stream = blob_client.download_blob()
                data = stream.readall()
                logger.info(f"Successfully fetched blob {name}, size: {len(data)} bytes")
                
                # Determine content type
                media_type = 'audio/mpeg'  # default
                if name.endswith('.wav'):
                    media_type = 'audio/wav'
                elif name.endswith('.ogg'):
                    media_type = 'audio/ogg'
                elif name.endswith('.webm'):
                    media_type = 'audio/webm'
                
                return StreamingResponse(
                    io.BytesIO(data), 
                    media_type=media_type,
                    headers={
                        'Content-Disposition': f'inline; filename="{name}"',
                        'Cache-Control': 'public, max-age=3600'
                    }
                )
        except Exception as e:
            logger.warning(f"Azure blob fetch failed for {name}: {e}")
            # Fall through to local file fallback

    # Local file fallback (served from backend/storage)
    local_path = STORAGE_DIR / name
    if local_path.exists():
        logger.info(f"Serving local file: {local_path}")
        
        # Determine media type based on file extension (same as /storage endpoint)
        media_type = "audio/mpeg"  # default for .mp3
        if name.endswith('.wav'):
            media_type = "audio/wav"
        elif name.endswith('.ogg'):
            media_type = "audio/ogg"
        elif name.endswith('.webm'):
            media_type = "audio/webm"
        
        return FileResponse(
            path=str(local_path),
            media_type=media_type,
            filename=name,
            headers={'Cache-Control': 'public, max-age=3600'}
        )

    logger.error(f"Audio file not found: {name}")
    raise HTTPException(status_code=404, detail='Audio not found')


@app.post("/api/voice-sample")
async def upload_voice_sample(file: UploadFile = File(...), name: str = ""):
    """Upload a voice sample for later use with TTS voice cloning."""
    try:
        logger.info(f"Received voice sample upload: name={name}, filename={file.filename}, content_type={file.content_type}")
        
        # Validate name
        if not name or not name.strip():
            name = file.filename.rsplit('.', 1)[0] if file.filename else f"voice_{int(time.time())}"
        
        # Determine file extension
        ext = '.webm'
        if file.content_type:
            if 'wav' in file.content_type.lower():
                ext = '.wav'
            elif 'mp3' in file.content_type.lower():
                ext = '.mp3'
            elif 'ogg' in file.content_type.lower():
                ext = '.ogg'
        elif file.filename:
            file_ext = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else ''
            if file_ext.lower() in ['wav', 'mp3', 'ogg', 'webm']:
                ext = f'.{file_ext.lower()}'
        
        # Generate unique voice ID
        voice_id = f"{name.strip().replace(' ', '_')}_{int(time.time())}"
        file_path = VOICES_DIR / f"{voice_id}{ext}"
        
        # Save the file
        content = await file.read()
        file_path.write_bytes(content)
        logger.info(f"Saved voice sample to {file_path} ({len(content)} bytes)")
        
        return {
            "ok": True,
            "voice_id": voice_id,
            "name": name,
            "path": str(file_path),
            "size_bytes": len(content)
        }
    except Exception as e:
        logger.error(f"Failed to upload voice sample: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/voices", dependencies=[Depends(verify_auth)])
async def list_voices():
    """List all available voice samples."""
    try:
        voices = []
        if VOICES_DIR.exists():
            for voice_file in VOICES_DIR.iterdir():
                if voice_file.is_file():
                    voices.append({
                        "id": voice_file.stem,
                        "name": voice_file.stem.rsplit('_', 1)[0],
                        "format": voice_file.suffix[1:],
                        "size_bytes": voice_file.stat().st_size,
                        "created": voice_file.stat().st_ctime
                    })
        logger.info(f"Listed {len(voices)} voice samples")
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Failed to list voices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@app.post("/api/clone-voice", dependencies=[Depends(verify_auth)])
async def clone_voice(voice_id: str, name: str = ""):
    """Clone a voice using ElevenLabs API from uploaded voice sample."""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
    
    # Find the voice file (try different extensions)
    voice_file = None
    for ext in ['.webm', '.wav', '.mp3', '.ogg']:
        candidate = VOICES_DIR / f"{voice_id}{ext}"
        if candidate.exists():
            voice_file = candidate
            break
    
    if not voice_file:
        raise HTTPException(status_code=404, detail=f"Voice sample {voice_id} not found")
    
    logger.info(f"Cloning voice from {voice_file}")
    
    try:
        # Upload to ElevenLabs
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        
        with open(voice_file, "rb") as f:
            files = {"files": (voice_file.name, f, "audio/webm")}
            data = {
                "name": name or voice_id,
                "description": f"Cloned voice from {voice_id}"
            }
            
            response = requests.post(
                "https://api.elevenlabs.io/v1/voices/add",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
            # Log the error details
            if not response.ok:
                error_detail = response.text
                logger.error(f"ElevenLabs API error {response.status_code}: {error_detail}")
                
                # Parse common errors
                if response.status_code == 400:
                    if "too short" in error_detail.lower() or "duration" in error_detail.lower():
                        raise HTTPException(status_code=400, detail="Audio too short. Please record at least 30 seconds.")
                    elif "limit" in error_detail.lower() or "quota" in error_detail.lower():
                        raise HTTPException(status_code=400, detail="Voice cloning limit reached. Delete old voices first.")
                    elif "format" in error_detail.lower():
                        raise HTTPException(status_code=400, detail="Audio format not supported. Try recording again.")
                    else:
                        raise HTTPException(status_code=400, detail=f"ElevenLabs error: {error_detail}")
                
                response.raise_for_status()
        
        result = response.json()
        elevenlabs_voice_id = result["voice_id"]
        
        # Save mapping to config
        config_file = STORAGE_DIR / "config.json"
        if config_file.exists():
            config = json.loads(config_file.read_text())
        else:
            config = {"voices": [], "cloned_voices": {}}
        
        if "cloned_voices" not in config:
            config["cloned_voices"] = {}
        
        from datetime import datetime
        config["cloned_voices"][voice_id] = {
            "elevenlabs_id": elevenlabs_voice_id,
            "name": name or voice_id,
            "created_at": datetime.now().isoformat()
        }
        
        config_file.write_text(json.dumps(config, indent=2))
        
        logger.info(f"Voice cloned successfully: {voice_id} -> {elevenlabs_voice_id}")
        return {
            "ok": True,
            "voice_id": voice_id,
            "elevenlabs_id": elevenlabs_voice_id,
            "name": name or voice_id
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"ElevenLabs API error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")
    except Exception as e:
        logger.error(f"Voice cloning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@app.get("/api/cloned-voices", dependencies=[Depends(verify_auth)])
async def get_cloned_voices():
    """Return list of cloned voices, synced with ElevenLabs."""
    try:
        # Fetch voices from ElevenLabs API
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        elevenlabs_voices = response.json().get("voices", [])
        
        # Filter to only cloned voices (not premade ones)
        cloned_from_api = [
            v for v in elevenlabs_voices 
            if v.get("category") == "cloned"
        ]
        
        # Load local config
        config_file = STORAGE_DIR / "config.json"
        if config_file.exists():
            config = json.loads(config_file.read_text())
            local_cloned = config.get("cloned_voices", {})
        else:
            local_cloned = {}
        
        # Merge: Use ElevenLabs as source of truth, enhance with local metadata
        cloned_voices = {}
        
        for el_voice in cloned_from_api:
            el_id = el_voice["voice_id"]
            el_name = el_voice["name"]
            
            # Find matching local entry
            local_match = None
            for vid, info in local_cloned.items():
                if info.get("elevenlabs_id") == el_id:
                    local_match = (vid, info)
                    break
            
            if local_match:
                voice_id, info = local_match
                cloned_voices[voice_id] = {
                    "elevenlabs_id": el_id,
                    "name": info.get("name", el_name),
                    "created_at": info.get("created_at", "")
                }
            else:
                # Voice exists in ElevenLabs but not in local config
                cloned_voices[el_name] = {
                    "elevenlabs_id": el_id,
                    "name": el_name,
                    "created_at": ""
                }
        
        # Format for frontend
        voices = [
            {
                "id": voice_id,
                "name": data["name"],
                "elevenlabs_id": data["elevenlabs_id"],
                "created_at": data.get("created_at", "")
            }
            for voice_id, data in cloned_voices.items()
        ]
        
        return {"cloned_voices": voices}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch ElevenLabs voices: {e}")
        # Fallback to local config
        config_file = STORAGE_DIR / "config.json"
        if not config_file.exists():
            return {"cloned_voices": []}
        
        config = json.loads(config_file.read_text())
        cloned_voices = config.get("cloned_voices", {})
        
        voices = [
            {
                "id": voice_id,
                "name": data["name"],
                "elevenlabs_id": data["elevenlabs_id"],
                "created_at": data.get("created_at", "")
            }
            for voice_id, data in cloned_voices.items()
        ]
        
        return {"cloned_voices": voices}


@app.delete("/api/delete-cloned-voice", dependencies=[Depends(verify_auth)])
async def delete_cloned_voice(voice_id: str):
    """Delete a cloned voice from config and ElevenLabs."""
    config_file = STORAGE_DIR / "config.json"
    if not config_file.exists():
        raise HTTPException(status_code=404, detail="No voices found")
    
    config = json.loads(config_file.read_text())
    cloned_voices = config.get("cloned_voices", {})
    
    if voice_id not in cloned_voices:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    
    elevenlabs_id = cloned_voices[voice_id]["elevenlabs_id"]
    
    # Delete from ElevenLabs (optional - may want to keep for reuse)
    if ELEVENLABS_API_KEY:
        try:
            headers = {"xi-api-key": ELEVENLABS_API_KEY}
            response = requests.delete(
                f"https://api.elevenlabs.io/v1/voices/{elevenlabs_id}",
                headers=headers,
                timeout=10
            )
            # Don't fail if ElevenLabs delete fails
            if response.ok:
                logger.info(f"Deleted voice from ElevenLabs: {elevenlabs_id}")
            else:
                logger.warning(f"Failed to delete from ElevenLabs: {response.status_code}")
        except Exception as e:
            logger.warning(f"ElevenLabs delete error: {e}")
    
    # Delete from config
    del cloned_voices[voice_id]
    config["cloned_voices"] = cloned_voices
    config_file.write_text(json.dumps(config, indent=2))
    
    # Delete voice sample file if exists
    for ext in ['.webm', '.wav', '.mp3', '.ogg']:
        voice_file = VOICES_DIR / f"{voice_id}{ext}"
        if voice_file.exists():
            voice_file.unlink()
            logger.info(f"Deleted voice file: {voice_file}")
            break
    
    logger.info(f"Voice deleted: {voice_id}")
    return {"ok": True, "deleted_voice_id": voice_id}


@app.get("/api/config", dependencies=[Depends(verify_auth)])
async def get_config():
    cfg_file = STORAGE_DIR / "config.json"
    if not cfg_file.exists():
        return {"voices": ["default", "female_1", "male_1"], "settings": {}}
    return json.loads(cfg_file.read_text())


@app.post("/api/config", dependencies=[Depends(verify_auth)])
async def save_config(payload: dict):
    cfg_file = STORAGE_DIR / "config.json"
    cfg_file.write_text(json.dumps(payload, indent=2))
    return {"ok": True}


@app.get("/health")
async def health():
    """Simple health endpoint used for readiness checks."""
    uptime = int(time.time() - START_TIME)
    blob_ok = bool(_blob_service)
    return {"status": "ok", "uptime_seconds": uptime, "azure_blob_configured": blob_ok}


@app.get("/storage/{filename}", dependencies=[Depends(verify_auth)])
async def serve_audio(filename: str):
    """Serve audio files with proper CORS headers for cross-origin playback."""
    file_path = STORAGE_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    media_type = "audio/mpeg"  # default for .mp3
    if filename.endswith('.wav'):
        media_type = "audio/wav"
    elif filename.endswith('.ogg'):
        media_type = "audio/ogg"
    elif filename.endswith('.webm'):
        media_type = "audio/webm"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

# Mount the static frontend so a single server can serve both (mounted after API routes)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
