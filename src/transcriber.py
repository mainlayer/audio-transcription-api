"""
Mock audio transcriber.

Replace `transcribe` with a real ASR backend (e.g. OpenAI Whisper,
AssemblyAI, AWS Transcribe, or Deepgram) for production use.
"""

from dataclasses import dataclass

SAMPLE_TRANSCRIPT = (
    "Welcome to the Mainlayer audio transcription service. "
    "This transcript is a placeholder demonstrating the API response format. "
    "In production, this text would be the actual speech-to-text output from your audio file. "
    "The service supports MP3, WAV, FLAC, OGG, and M4A audio formats and bills "
    "per minute of audio processed."
)


@dataclass
class TranscriptResult:
    text: str
    duration_seconds: float
    language: str
    confidence: float
    word_count: int


def estimate_duration(file_bytes: bytes, content_type: str) -> float:
    """
    Estimate audio duration from file size.

    Very rough heuristic — real implementations should decode the audio header.
    Assumes ~128 kbps average bitrate.
    """
    bits = len(file_bytes) * 8
    assumed_bitrate = 128_000  # bits per second
    seconds = bits / assumed_bitrate
    return max(1.0, round(seconds, 2))


def transcribe(file_bytes: bytes, content_type: str, language: str = "en") -> TranscriptResult:
    """
    Transcribe audio bytes (mock implementation).

    Args:
        file_bytes:   Raw audio file content.
        content_type: MIME type of the audio file.
        language:     BCP-47 language hint (e.g. 'en', 'fr', 'es').

    Returns:
        TranscriptResult with transcript text and metadata.
    """
    duration = estimate_duration(file_bytes, content_type)
    text = SAMPLE_TRANSCRIPT

    return TranscriptResult(
        text=text,
        duration_seconds=duration,
        language=language,
        confidence=0.94,
        word_count=len(text.split()),
    )
