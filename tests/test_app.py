from collections.abc import Iterator

from fastapi.testclient import TestClient

import app.main as main
from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_serves_playground() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    body = response.text
    assert "LiteLLM Playground" in body
    assert 'data-tab="chat"' in body
    assert 'data-tab="speech"' in body
    assert 'data-tab="transcribe"' in body
    assert 'data-tab="decisions"' in body


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


def test_models_endpoint_returns_list(monkeypatch) -> None:
    monkeypatch.setattr(main, "list_chat_models", lambda: ["gpt-5.5", "claude-haiku-4-5"])
    client = TestClient(app)

    response = client.get("/api/models")

    assert response.status_code == 200
    assert response.json() == {"models": ["gpt-5.5", "claude-haiku-4-5"]}


def test_chat_endpoint_streams_text(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_stream_chat(*, model: str, messages: list[dict[str, str]]) -> Iterator[str]:
        captured["model"] = model
        captured["messages"] = messages
        yield "Hel"
        yield "lo!"

    monkeypatch.setattr(main, "stream_chat", fake_stream_chat)
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={
            "model": "claude-haiku-4-5",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Hello!"
    assert captured == {
        "model": "claude-haiku-4-5",
        "messages": [{"role": "user", "content": "hi"}],
    }


def test_chat_endpoint_rejects_invalid_role() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={
            "model": "claude-haiku-4-5",
            "messages": [{"role": "bogus", "content": "hi"}],
        },
    )

    assert response.status_code == 422


def test_decisions_endpoint_returns_answers(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_make_decisions(*, text: str, questions: list[dict[str, object]]) -> dict[str, object]:
        captured["text"] = text
        captured["questions"] = questions
        return {"model": "gpt-6-luna", "answers": [{"type": "predicate", "name": "q", "probability": 0.9}]}

    monkeypatch.setattr(main, "make_decisions", fake_make_decisions)
    client = TestClient(app)
    questions = [{"type": "predicate", "name": "q", "instructions": "Is it urgent?"}]

    response = client.post("/api/decisions", json={"input": "BP 182/110", "questions": questions})

    assert response.status_code == 200
    assert response.json()["answers"][0]["probability"] == 0.9
    assert captured == {"text": "BP 182/110", "questions": questions}


def test_decisions_endpoint_rejects_empty_questions() -> None:
    client = TestClient(app)

    response = client.post("/api/decisions", json={"input": "hi", "questions": []})

    assert response.status_code == 422
