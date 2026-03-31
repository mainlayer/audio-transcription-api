# audio-transcription-api

[![CI](https://github.com/mainlayer/audio-transcription-api/actions/workflows/ci.yml/badge.svg)](https://github.com/mainlayer/audio-transcription-api/actions/workflows/ci.yml)

A FastAPI service that converts speech to text with **per-minute credit billing** via [Mainlayer](https://mainlayer.fr).

## Features

- `POST /transcribe` — upload an audio file and receive a transcript
- Per-minute billing: partial minutes rounded up (1 credit = 1 minute)
- Supports MP3, WAV, FLAC, OGG, and M4A audio formats
- Language hint parameter for improved accuracy
- Confidence score and word count returned with every transcript

## Quickstart

```bash
pip install mainlayer
```

```bash
export MAINLAYER_API_KEY=your_api_key
export MAINLAYER_RESOURCE_ID=your_resource_id
uvicorn src.main:app --reload
```

### Transcribe an audio file

```python
import httpx

with open("meeting.mp3", "rb") as f:
    resp = httpx.post(
        "http://localhost:8000/transcribe",
        files={"file": ("meeting.mp3", f, "audio/mpeg")},
        data={"language": "en"},
        headers={"x-mainlayer-token": "<your-token>"},
        timeout=120,
    )

data = resp.json()
print(data["text"])
print(f"Duration: {data['duration_seconds']:.1f}s, Credits: {data['credits_used']}")
```

## API Reference

### `POST /transcribe`

**Headers:** `x-mainlayer-token` (required)

**Body:** multipart form

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | file | required | Audio file (MP3, WAV, FLAC, OGG, M4A) |
| `language` | string | `en` | BCP-47 language code |

**Response:**
```json
{
  "text": "Welcome to the meeting. Today we will discuss...",
  "duration_seconds": 127.4,
  "language": "en",
  "confidence": 0.94,
  "word_count": 312,
  "credits_used": 3.0
}
```

## Billing

Credits are charged per minute of audio, with partial minutes rounded up:
- 1–60 seconds → 1 credit
- 61–120 seconds → 2 credits
- etc.

## Payment

Access is gated through Mainlayer payment tokens. Get your token at [mainlayer.fr](https://mainlayer.fr).

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```
