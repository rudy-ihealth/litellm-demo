from collections.abc import Iterator

import openai

from app.config import Settings, get_settings

AUDIO_MODEL_HINTS = ("tts", "transcribe", "whisper")


def _create_client(settings: Settings) -> openai.OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    if settings.openai_base_url is None:
        raise RuntimeError("OPENAI_BASE_URL is not configured.")

    return openai.OpenAI(
        api_key=settings.openai_api_key,
        base_url=str(settings.openai_base_url),
    )


def list_chat_models() -> list[str]:
    settings = get_settings()
    client = _create_client(settings)

    models = client.models.list()
    ids = sorted(m.id for m in models.data)
    return [m for m in ids if not any(hint in m.lower() for hint in AUDIO_MODEL_HINTS)]


def stream_chat(*, model: str, messages: list[dict[str, str]]) -> Iterator[str]:
    settings = get_settings()
    client = _create_client(settings)

    chunks = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    for chunk in chunks:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
