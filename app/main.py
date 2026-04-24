from pathlib import Path

import openai
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.audio import synthesize_speech, transcribe_audio

app = FastAPI()
STATIC_DIR = Path(__file__).parent / "static"


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    voice: str = Field(min_length=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/tts")
def create_tts(payload: TTSRequest) -> Response:
    try:
        audio_bytes = synthesize_speech(
            text=payload.text,
            voice=payload.voice,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except openai.OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"TTS request failed: {exc}") from exc

    return Response(content=audio_bytes, media_type="audio/mpeg")


@app.post("/api/transcribe")
async def create_transcription(file: UploadFile = File(...)) -> dict[str, str]:
    try:
        transcript = transcribe_audio(
            filename=file.filename or "audio",
            content=await file.read(),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except openai.OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"Transcription request failed: {exc}") from exc

    return {"text": transcript}
