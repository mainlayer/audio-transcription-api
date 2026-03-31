import os
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MAINLAYER_API_KEY", "test-key")
os.environ.setdefault("MAINLAYER_RESOURCE_ID", "test-resource")

# Minimal valid WAV header (44 bytes, empty PCM data)
MINIMAL_WAV = (
    b"RIFF\x24\x00\x00\x00WAVEfmt "
    b"\x10\x00\x00\x00\x01\x00\x01\x00"
    b"\x44\xac\x00\x00\x88\x58\x01\x00"
    b"\x02\x00\x10\x00data\x00\x00\x00\x00"
)


def _make_app():
    with patch("mainlayer.MainlayerClient"):
        from src.main import app
        return app


@pytest.fixture()
def authorized_client():
    app = _make_app()
    access_mock = MagicMock()
    access_mock.authorized = True
    with patch("src.main.ml") as ml_mock:
        ml_mock.resources.verify_access = AsyncMock(return_value=access_mock)
        with TestClient(app) as client:
            yield client


@pytest.fixture()
def unauthorized_client():
    app = _make_app()
    access_mock = MagicMock()
    access_mock.authorized = False
    with patch("src.main.ml") as ml_mock:
        ml_mock.resources.verify_access = AsyncMock(return_value=access_mock)
        with TestClient(app) as client:
            yield client


def test_health():
    app = _make_app()
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200


def test_transcribe_authorized(authorized_client):
    resp = authorized_client.post(
        "/transcribe",
        files={"file": ("audio.wav", MINIMAL_WAV, "audio/wav")},
        data={"language": "en"},
        headers={"x-mainlayer-token": "valid-token"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert data["word_count"] > 0
    assert data["credits_used"] >= 1


def test_transcribe_unauthorized(unauthorized_client):
    resp = unauthorized_client.post(
        "/transcribe",
        files={"file": ("audio.wav", MINIMAL_WAV, "audio/wav")},
        data={"language": "en"},
        headers={"x-mainlayer-token": "bad-token"},
    )
    assert resp.status_code == 402


def test_transcribe_missing_token():
    app = _make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/transcribe",
            files={"file": ("audio.wav", MINIMAL_WAV, "audio/wav")},
        )
    assert resp.status_code == 422


def test_transcribe_unsupported_type(authorized_client):
    resp = authorized_client.post(
        "/transcribe",
        files={"file": ("video.mp4", b"\x00\x01\x02", "video/mp4")},
        data={"language": "en"},
        headers={"x-mainlayer-token": "valid-token"},
    )
    assert resp.status_code == 415


def test_transcribe_empty_file(authorized_client):
    resp = authorized_client.post(
        "/transcribe",
        files={"file": ("empty.wav", b"", "audio/wav")},
        data={"language": "en"},
        headers={"x-mainlayer-token": "valid-token"},
    )
    assert resp.status_code == 400


# --- Billing unit tests ---

def test_calculate_credits_one_minute():
    from src.billing import calculate_credits
    assert calculate_credits(60.0) == 1.0


def test_calculate_credits_partial_minute_rounds_up():
    from src.billing import calculate_credits
    assert calculate_credits(61.0) == 2.0
    assert calculate_credits(1.0) == 1.0


def test_calculate_credits_custom_price():
    from src.billing import calculate_credits
    assert calculate_credits(120.0, price_per_minute=0.5) == 1.0


def test_calculate_credits_three_minutes():
    from src.billing import calculate_credits
    assert calculate_credits(180.0) == 3.0
