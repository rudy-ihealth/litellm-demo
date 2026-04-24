# LiteLLM Audio Demo

Small FastAPI app that uses `openai.OpenAI` against a LiteLLM/OpenAI-compatible endpoint and serves a browser UI for text-to-speech and audio transcription.

## Why this shape

- `uv` manages the Python environment locally.
- FastAPI exposes a small JSON API and serves the frontend from the same container.
- Docker Compose gives you a clean, repeatable runtime with the same dependency set as local dev.

## Prerequisites

- `uv`
- Docker + Docker Compose
- A valid LiteLLM/OpenAI-compatible API key and endpoint

## Configure

```bash
cp .env.example .env
```

Then edit `.env` and set:

```env
OPENAI_API_KEY=your-real-key
OPENAI_BASE_URL=https://your-litellm-host
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TRANSCRIBE_MODEL=gpt-4o-transcribe
```

The key shown in your original message should be treated as exposed. Rotate it before using this app.

## Run locally with uv

```bash
uv sync --dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Run with Docker Compose

```bash
docker compose up --build
```

Open `http://localhost:8000`.

## Test

```bash
uv run pytest -q
```

## Health check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Equivalent Python usage

Text-to-speech:

```python
import os
import openai

client = openai.OpenAI(
    api_key="your-real-key",
    base_url=os.environ["OPENAI_BASE_URL"],
)

response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    input="Your text to convert to speech here",
    voice="alloy",
)

response.stream_to_file("output_speech.mp3")
```

Transcription:

```python
import os
import openai

client = openai.OpenAI(
    api_key="your-real-key",
    base_url=os.environ["OPENAI_BASE_URL"],
)

audio_file = open("path/to/your/audio/file.mp3", "rb")

response = client.audio.transcriptions.create(
    model="gpt-4o-transcribe",
    file=audio_file,
)

print(response.text)
```

## Notes

- The app returns MP3 bytes from `/api/tts`.
- The app returns transcript JSON from `/api/transcribe`.
- The frontend lets you choose a built-in voice.
- OpenAI’s current text-to-speech docs show `gpt-4o-mini-tts` on the speech endpoint and list `alloy` among the supported voices.
