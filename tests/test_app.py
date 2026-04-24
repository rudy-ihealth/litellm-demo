from fastapi.testclient import TestClient

import app.main as main
from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_serves_form() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Generate speech" in response.text
    assert "Transcribe audio" in response.text


def test_tts_endpoint_returns_audio_bytes(monkeypatch) -> None:
    def fake_synthesize_speech(*, text: str, voice: str) -> bytes:
        assert text == "hello"
        assert voice == "alloy"
        return b"fake-mp3"

    monkeypatch.setattr(main, "synthesize_speech", fake_synthesize_speech)
    client = TestClient(app)

    response = client.post(
        "/api/tts",
        json={"text": "hello", "voice": "alloy"},
    )

    assert response.status_code == 200
    assert response.content == b"fake-mp3"
    assert response.headers["content-type"] == "audio/mpeg"


def test_transcribe_endpoint_returns_text(monkeypatch) -> None:
    def fake_transcribe_audio(*, filename: str, content: bytes) -> str:
        assert filename == "sample.mp3"
        assert content == b"fake-audio"
        return "hello transcript"

    monkeypatch.setattr(main, "transcribe_audio", fake_transcribe_audio)
    client = TestClient(app)

    response = client.post(
        "/api/transcribe",
        files={"file": ("sample.mp3", b"fake-audio", "audio/mpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "hello transcript"}
