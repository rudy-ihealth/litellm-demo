# LiteLLM Playground

Small FastAPI app that uses `openai.OpenAI` against a LiteLLM/OpenAI-compatible endpoint and serves a tabbed browser UI for chat (streaming), text-to-speech, and audio transcription.

![LiteLLM Playground — chat tab streaming a reply from claude-haiku-4-5](docs/test-webpage.png)

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

Chat completion:

```python
import os
import openai

client = openai.OpenAI(
    api_key="your-real-key",
    base_url=os.environ["OPENAI_BASE_URL"],
)

response = client.chat.completions.create(
    model="claude-haiku-4-5",
    messages=[
        {"role": "system", "content": "You are a terse assistant."},
        {"role": "user", "content": "Name a primary color."},
    ],
)

print(response.choices[0].message.content)
```

Streaming chat completion:

```python
import os
import openai

client = openai.OpenAI(
    api_key="your-real-key",
    base_url=os.environ["OPENAI_BASE_URL"],
)

stream = client.chat.completions.create(
    model="gpt-5.5",
    messages=[{"role": "user", "content": "Write a 3-line haiku about streaming."}],
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta.content if chunk.choices else None
    if delta:
        print(delta, end="", flush=True)
print()
```

List available models:

```python
import os
import openai

client = openai.OpenAI(
    api_key="your-real-key",
    base_url=os.environ["OPENAI_BASE_URL"],
)

for model in client.models.list().data:
    print(model.id)
```

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

## Endpoints

| Method | Path | Returns |
| --- | --- | --- |
| GET  | `/health` | `{"status":"ok"}` |
| GET  | `/api/models` | `{"models": [...]}` — chat-capable models from the proxy |
| POST | `/api/chat` | streaming `text/plain` deltas; body `{"model","messages":[{"role","content"}]}` |
| POST | `/api/tts` | MP3 bytes; body `{"text","voice"}` |
| POST | `/api/transcribe` | `{"text": ...}`; multipart `file` upload |

## Notes

- The frontend is a single static page with three tabs (Chat / Speech / Transcribe).
- Chat streams via `response.body.getReader()` against `/api/chat`. Conversation history is kept client-side.
- OpenAI's current text-to-speech docs show `gpt-4o-mini-tts` on the speech endpoint and list `alloy` among the supported voices.
