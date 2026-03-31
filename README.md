# Audio Transcription API

A production-ready speech-to-text service with per-minute billing via [Mainlayer](https://mainlayer.fr).

## Features

- **Multiple audio formats**: MP3, WAV, FLAC, OGG, M4A
- **10+ languages**: English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Japanese, Mandarin
- **Per-minute billing**: Partial minutes rounded up (30 seconds = $1, 61 seconds = $2)
- **Confidence scores**: Quality metrics for each transcript
- **Production-ready**: Structured logging, error handling, comprehensive docs

## Pricing

| Operation | Cost |
|-----------|------|
| Transcription | $1.00 per minute (rounded up) |
| Health check | FREE |
| List languages | FREE |

## 5-Minute Quickstart

### 1. Install dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set environment variables

```bash
export MAINLAYER_API_KEY=your_api_key
export MAINLAYER_RESOURCE_ID=your_resource_id
export LOG_LEVEL=INFO
```

### 3. Start the server

```bash
uvicorn src.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`

### 4. Check supported languages

```bash
curl http://localhost:8000/languages
```

Response:
```json
{
  "supported_languages": ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "zh"],
  "default_language": "en"
}
```

### 5. Transcribe an audio file

```bash
curl -X POST http://localhost:8000/transcribe \
  -H "X-Mainlayer-Token: your_payment_token" \
  -F "file=@meeting.mp3" \
  -F "language=en"
```

Response:
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

## API Reference

### `POST /transcribe`

Transcribe an audio file to text.

**Headers**:
- `X-Mainlayer-Token`: Mainlayer payment token (required)

**Body** (multipart/form-data):
- `file`: Audio file to transcribe (required; MP3, WAV, FLAC, OGG, M4A)
- `language`: BCP-47 language code (default: `en`)

**Response**:
```json
{
  "text": "string",
  "duration_seconds": 127.4,
  "language": "en",
  "confidence": 0.94,
  "word_count": 312,
  "credits_used": 3.0
}
```

**Cost**: $1.00 per minute (rounded up)

**Status Codes**:
- `200`: Transcription completed
- `400`: Empty file or invalid parameters
- `402`: Payment required or invalid token
- `413`: File exceeds 200 MB limit
- `415`: Unsupported audio format
- `500`: Transcription engine error

---

### `GET /languages`

List supported languages for transcription (FREE).

**Response**:
```json
{
  "supported_languages": [
    "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "zh"
  ],
  "default_language": "en"
}
```

**Cost**: FREE

---

### `GET /health`

Health check endpoint.

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Cost**: FREE

---

## Billing Details

### Per-Minute Rounding

Billing rounds partial minutes up to the next whole minute:

| Audio Duration | Billed as | Cost |
|---|---|---|
| 1–60 seconds | 1 minute | $1.00 |
| 61–120 seconds | 2 minutes | $2.00 |
| 121–180 seconds | 3 minutes | $3.00 |
| 30 seconds (minimum) | 1 minute | $1.00 |

### Example Billing Scenarios

**Meeting recording (5 min 45 sec)**:
- Billed as: 6 minutes
- Cost: $6.00

**Voicemail (30 sec)**:
- Billed as: 1 minute
- Cost: $1.00

**Webinar (1 hour 23 min 15 sec)**:
- Billed as: 84 minutes
- Cost: $84.00

---

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English (default) |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `nl` | Dutch |
| `ru` | Russian |
| `ja` | Japanese |
| `zh` | Mandarin Chinese |

---

## Supported Audio Formats

| Format | MIME Type | Extension |
|--------|-----------|-----------|
| MP3 | `audio/mpeg` | `.mp3` |
| WAV | `audio/wav` | `.wav` |
| FLAC | `audio/flac` | `.flac` |
| OGG | `audio/ogg` | `.ogg` |
| M4A | `audio/x-m4a` | `.m4a` |

---

## Examples

### Python client

```python
import httpx

with open("meeting.mp3", "rb") as f:
    resp = httpx.post(
        "http://localhost:8000/transcribe",
        files={"file": ("meeting.mp3", f, "audio/mpeg")},
        data={"language": "en"},
        headers={"X-Mainlayer-Token": "your_token"},
        timeout=120,
    )

data = resp.json()
print(f"Text: {data['text']}")
print(f"Duration: {data['duration_seconds']:.1f}s")
print(f"Cost: ${data['credits_used']:.2f}")
```

### JavaScript/Node.js

```javascript
import FormData from 'form-data';
import fs from 'fs';
import axios from 'axios';

const form = new FormData();
form.append('file', fs.createReadStream('meeting.mp3'), 'meeting.mp3');
form.append('language', 'en');

const response = await axios.post(
  'http://localhost:8000/transcribe',
  form,
  {
    headers: {
      ...form.getHeaders(),
      'X-Mainlayer-Token': 'your_token',
    },
  }
);

console.log(response.data.text);
console.log(`Duration: ${response.data.duration_seconds}s`);
console.log(`Cost: $${response.data.credits_used}`);
```

### cURL

```bash
curl -X POST http://localhost:8000/transcribe \
  -H "X-Mainlayer-Token: your_token" \
  -F "file=@meeting.mp3" \
  -F "language=en" | jq '.text'
```

---

## Limits

| Limit | Value |
|-------|-------|
| Max file size | 200 MB |
| Min audio duration | 0.5 seconds |
| Max audio duration | 1 hour (3600 seconds) |
| Request timeout | 120 seconds |

---

## Development

### Running tests

```bash
pytest tests/ -v
```

### Docker deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY src/ src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: audio-transcription-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: audio-transcription-api
  template:
    metadata:
      labels:
        app: audio-transcription-api
    spec:
      containers:
      - name: api
        image: audio-transcription-api:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "500m"
            memory: "256Mi"
```

---

## Production Checklist

- [ ] Configure HTTPS/TLS
- [ ] Enable CORS (restrict origins)
- [ ] Set up request logging
- [ ] Configure rate limiting per token
- [ ] Add Prometheus metrics
- [ ] Enable distributed tracing
- [ ] Test with live Mainlayer account
- [ ] Configure auto-scaling
- [ ] Set up monitoring and alerting
- [ ] Document SLA and uptime targets
- [ ] Integrate real transcription backend (Whisper, AssemblyAI, etc.)

---

## Integration with Real ASR Engines

### OpenAI Whisper

```python
import openai

def transcribe_with_whisper(file_bytes: bytes) -> str:
    transcript = openai.Audio.transcribe("whisper-1", file_bytes)
    return transcript["text"]
```

### AssemblyAI

```python
import httpx

async def transcribe_with_assemblyai(file_bytes: bytes, language: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.assemblyai.com/v2/transcript",
            json={
                "audio_url": "...",
                "language_code": language,
            },
            headers={"Authorization": ASSEMBLYAI_TOKEN},
        )
    return resp.json()["text"]
```

---

## Support

- Docs: https://docs.mainlayer.fr
- Issues: https://github.com/mainlayer/audio-transcription-api/issues
