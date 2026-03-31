"""
Example: transcribe an audio file via the Audio Transcription API.

Usage:
    MAINLAYER_TOKEN=<token> python examples/transcribe_audio.py [path/to/audio.mp3]
"""

import os
import sys
import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
TOKEN = os.getenv("MAINLAYER_TOKEN")

if not TOKEN:
    print("Error: set MAINLAYER_TOKEN environment variable")
    sys.exit(1)


def main() -> None:
    file_path = sys.argv[1] if len(sys.argv) > 1 else None

    if file_path:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
        filename = os.path.basename(file_path)
        content_type = "audio/mpeg" if file_path.endswith(".mp3") else "audio/wav"
    else:
        # Minimal WAV header (44 bytes) for demo purposes
        audio_bytes = bytes(44)
        filename = "demo.wav"
        content_type = "audio/wav"

    resp = httpx.post(
        f"{API_BASE}/transcribe",
        files={"file": (filename, audio_bytes, content_type)},
        data={"language": "en"},
        headers={"x-mainlayer-token": TOKEN},
        timeout=120,
    )

    if resp.status_code == 402:
        print("Payment required — get access at https://mainlayer.fr")
        sys.exit(1)

    resp.raise_for_status()
    data = resp.json()

    print(f"Language    : {data['language']}")
    print(f"Duration    : {data['duration_seconds']:.1f}s")
    print(f"Words       : {data['word_count']}")
    print(f"Confidence  : {data['confidence']:.2%}")
    print(f"Credits used: {data['credits_used']}")
    print("\n--- Transcript ---")
    print(data["text"])


if __name__ == "__main__":
    main()
