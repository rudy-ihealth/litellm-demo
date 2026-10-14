# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Environment uses `uv` (Python 3.12+). `.env` required at repo root for runtime; tests do not need it.

```bash
uv sync --dev                                                  # install deps
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # local dev server
uv run pytest -q                                               # run all tests
uv run pytest tests/test_audio.py::test_synthesize_speech_uses_openai_base_url_client  # single test
docker compose up --build                                      # container run (uses .env)
```

## Architecture

FastAPI app proxying an OpenAI-compatible endpoint (LiteLLM/Azure) for TTS + transcription. Single container serves both JSON API and static frontend on port 8000.

- [app/main.py](app/main.py) — FastAPI routes. `/health`, `/` (serves [app/static/index.html](app/static/index.html)), `POST /api/tts` (`audio/mpeg`), `POST /api/transcribe` (multipart → `{"text": ...}`), `GET /api/models` (chat-capable proxy models), `POST /api/chat` (streaming `text/plain` chat completion), `POST /api/decisions` (Decisions API, JSON). `RuntimeError` → 500 (config), `openai.OpenAIError` → 502 (upstream). Note: `/api/chat` errors raised mid-stream are emitted inline as `[upstream error] ...` since headers are already sent.
- [app/audio.py](app/audio.py) — `synthesize_speech` / `transcribe_audio`. Builds `openai.OpenAI` per-call from settings; raises `RuntimeError` if `OPENAI_API_KEY` or `OPENAI_BASE_URL` missing.
- [app/chat.py](app/chat.py) — `list_chat_models()` (filters out audio models by name hints) and `stream_chat()` (generator yielding text deltas from `chat.completions.create(stream=True)`).
- [app/decisions.py](app/decisions.py) — `make_decisions()` calls `client.decisions.create` (OpenAI SDK v3) with `OPENAI_DECISIONS_MODEL` and returns the response as a dict.
- [app/config.py](app/config.py) — `pydantic-settings` `Settings` loaded from `.env`. `get_settings()` is `lru_cache`'d — tests must `cache_clear()` or monkeypatch `get_settings` directly when changing env.
- [app/static/index.html](app/static/index.html) — Self-contained tabbed frontend (Chat / Speech / Transcribe / Decisions), no build step. Chat tab loads model list from `/api/models`, streams `/api/chat` via `response.body.getReader()`, maintains `conversation` array client-side.

The OpenAI client is OpenAI-SDK-compatible against any base URL — `OPENAI_BASE_URL` points at LiteLLM/Azure, models are configurable via `OPENAI_TTS_MODEL` / `OPENAI_TRANSCRIBE_MODEL`.

## Testing notes

- `tests/test_app.py` monkeypatches `app.main.synthesize_speech` / `transcribe_audio` — bypasses the OpenAI client entirely.
- `tests/test_audio.py` monkeypatches `audio.openai.OpenAI` with a fake and overrides `audio.get_settings` to inject a `Settings` instance. Pattern: clear `FakeOpenAI.instances`, swap `OpenAI`, then call `cache_clear()` on `get_settings` if needed before patching.
- No mock of `.env` — tests inject `Settings(...)` directly.
