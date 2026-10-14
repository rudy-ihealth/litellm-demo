from typing import Any

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


def make_decisions(*, text: str, questions: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    client = _create_client(settings)

    response = client.decisions.create(
        model=settings.openai_decisions_model,
        input=text,
        questions=questions,
    )

    return response.model_dump(exclude_none=True)
