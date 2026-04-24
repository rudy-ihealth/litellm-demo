from app.config import Settings
import app.audio as audio


class FakeSpeech:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return type("FakeSpeechResponse", (), {"content": b"mp3"})()


class FakeAudio:
    def __init__(self) -> None:
        self.speech = FakeSpeech()
        self.transcriptions = FakeTranscriptions()


class FakeTranscriptions:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        return type("FakeTranscriptionResponse", (), {"text": "hello transcript"})()


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.audio = FakeAudio()
        self.instances.append(self)


def test_synthesize_speech_uses_openai_base_url_client(monkeypatch) -> None:
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(audio.openai, "OpenAI", FakeOpenAI)
    audio.get_settings.cache_clear()
    monkeypatch.setattr(
        audio,
        "get_settings",
        lambda: Settings(
            openai_api_key="test-key",
            openai_base_url="https://litellm.example.com",
            openai_tts_model="gpt-4o-mini-tts",
        ),
    )

    audio_bytes = audio.synthesize_speech(text="hello", voice="alloy")

    assert audio_bytes == b"mp3"
    assert FakeOpenAI.instances[0].kwargs == {
        "api_key": "test-key",
        "base_url": "https://litellm.example.com/",
    }
    assert FakeOpenAI.instances[0].audio.speech.kwargs == {
        "model": "gpt-4o-mini-tts",
        "input": "hello",
        "voice": "alloy",
    }


def test_transcribe_audio_uses_openai_transcription_model(monkeypatch) -> None:
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(audio.openai, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        audio,
        "get_settings",
        lambda: Settings(
            openai_api_key="test-key",
            openai_base_url="https://litellm.example.com",
            openai_transcribe_model="gpt-4o-transcribe",
        ),
    )

    transcript = audio.transcribe_audio(filename="audio.mp3", content=b"mp3")

    assert transcript == "hello transcript"
    assert FakeOpenAI.instances[0].audio.transcriptions.kwargs == {
        "model": "gpt-4o-transcribe",
        "file": ("audio.mp3", b"mp3"),
    }
