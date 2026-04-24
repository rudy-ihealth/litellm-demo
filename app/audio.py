import openai

from app.config import Settings, get_settings


def _create_client(settings: Settings) -> openai.OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    if settings.openai_base_url is None:
        raise RuntimeError("OPENAI_BASE_URL is not configured.")

    return openai.OpenAI(
        api_key=settings.openai_api_key,
        base_url=str(settings.openai_base_url),
    )


def synthesize_speech(*, text: str, voice: str) -> bytes:
    settings = get_settings()
    client = _create_client(settings)

    response = client.audio.speech.create(
        model=settings.openai_tts_model,
        input=text,
        voice=voice,
    )

    return response.content


def transcribe_audio(*, filename: str, content: bytes) -> str:
    settings = get_settings()
    client = _create_client(settings)

    response = client.audio.transcriptions.create(
        model=settings.openai_transcribe_model,
        file=(filename, content),
    )

    return response.text
