import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel, Field

from mainlayer import MainlayerClient
from src.transcriber import transcribe
from src.billing import calculate_credits

# Logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Audio Transcription API starting up")
    yield
    logger.info("Audio Transcription API shutting down")


app = FastAPI(
    title="Audio Transcription API",
    description="Per-minute billed audio transcription powered by Mainlayer",
    version="1.0.0",
    lifespan=lifespan,
)

ml = MainlayerClient(api_key=os.environ["MAINLAYER_API_KEY"])
RESOURCE_ID = os.environ["MAINLAYER_RESOURCE_ID"]

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
}

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


class TranscribeResponse(BaseModel):
    text: str = Field(..., description="Transcribed text from the audio")
    duration_seconds: float = Field(..., description="Duration of the audio in seconds")
    language: str = Field(..., description="Language code used for transcription")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    word_count: int = Field(..., description="Number of words in the transcript")
    credits_used: float = Field(..., description="Credits charged for this transcription")


class LanguageResponse(BaseModel):
    supported_languages: list[str]
    default_language: str


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/languages")
async def list_languages():
    """List supported languages for transcription (FREE)."""
    return LanguageResponse(
        supported_languages=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "zh"],
        default_language="en",
    )


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form("en", description="BCP-47 language code (e.g. en, fr, es)"),
    x_mainlayer_token: str = Header(..., description="Mainlayer payment token"),
):
    """
    Transcribe an audio file to text.

    **Cost**: $1.00 per minute (rounded up; 30 seconds = $1.00, 61 seconds = $2.00).

    **Supported Formats**: MP3, WAV, FLAC, OGG, M4A

    **Supported Languages**:
    - `en` (English) — default
    - `es` (Spanish)
    - `fr` (French)
    - `de` (German)
    - `it` (Italian)
    - `pt` (Portuguese)
    - `nl` (Dutch)
    - `ru` (Russian)
    - `ja` (Japanese)
    - `zh` (Mandarin Chinese)

    **Size Limits**:
    - Max file size: 200 MB
    - Min audio duration: 0.5 seconds
    - Max audio duration: 1 hour (3600 seconds)

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/transcribe \\
      -H "X-Mainlayer-Token: your_token" \\
      -F "file=@audio.mp3" \\
      -F "language=en"
    ```
    """
    # Verify payment
    try:
        access = await ml.resources.verify_access(RESOURCE_ID, x_mainlayer_token)
    except Exception as exc:
        logger.error(f"Payment verification failed: {exc}")
        raise HTTPException(
            status_code=402,
            detail="Payment verification failed. Ensure your token is valid.",
        )

    if not access.authorized:
        logger.warning(f"Unauthorized transcription attempt with token {x_mainlayer_token[:10]}...")
        raise HTTPException(
            status_code=402,
            detail="Payment required. Get access at mainlayer.fr",
        )

    # Validate audio format
    content_type = file.content_type or ""
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported audio type '{content_type}'. "
                "Accepted: MP3, WAV, FLAC, OGG, M4A."
            ),
        )

    # Read and validate file
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_FILE_SIZE / (1024**2):.0f} MB limit.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Transcribe
    lang = language or "en"
    logger.info(f"Transcribing {len(file_bytes)} bytes, language={lang}")

    try:
        result = transcribe(file_bytes, content_type=content_type, language=lang)
    except Exception as exc:
        logger.error(f"Transcription failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Transcription failed. Please check your audio file and try again.",
        )

    # Calculate billing
    credits = calculate_credits(result.duration_seconds)
    logger.info(
        f"Transcription completed: {result.duration_seconds}s audio, "
        f"{result.word_count} words, ${credits:.2f} charged"
    )

    return TranscribeResponse(
        text=result.text,
        duration_seconds=result.duration_seconds,
        language=result.language,
        confidence=result.confidence,
        word_count=result.word_count,
        credits_used=credits,
    )
