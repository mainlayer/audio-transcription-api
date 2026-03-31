import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from mainlayer import MainlayerClient
from src.transcriber import transcribe
from src.billing import calculate_credits

app = FastAPI(
    title="Audio Transcription API",
    description="Per-minute billed audio transcription powered by Mainlayer",
    version="1.0.0",
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
    text: str
    duration_seconds: float
    language: str
    confidence: float
    word_count: int
    credits_used: float


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form("en", description="BCP-47 language code (e.g. en, fr, es)"),
    x_mainlayer_token: str = Header(..., description="Mainlayer payment token"),
):
    access = await ml.resources.verify_access(RESOURCE_ID, x_mainlayer_token)
    if not access.authorized:
        raise HTTPException(
            status_code=402,
            detail="Payment required. Get access at mainlayer.fr",
        )

    content_type = file.content_type or ""
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported audio type '{content_type}'. "
                "Accepted: MP3, WAV, FLAC, OGG, M4A."
            ),
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 200 MB limit.")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = transcribe(file_bytes, content_type=content_type, language=language or "en")
    credits = calculate_credits(result.duration_seconds)

    return TranscribeResponse(
        text=result.text,
        duration_seconds=result.duration_seconds,
        language=result.language,
        confidence=result.confidence,
        word_count=result.word_count,
        credits_used=credits,
    )
