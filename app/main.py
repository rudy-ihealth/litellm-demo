from pathlib import Path
from typing import Any, Literal

import openai
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from app.audio import synthesize_speech, transcribe_audio
from app.chat import list_chat_models, stream_chat
from app.decisions import make_decisions

app = FastAPI()
STATIC_DIR = Path(__file__).parent / "static"


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    voice: str = Field(min_length=1)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[ChatMessage] = Field(min_length=1)


class DecisionsRequest(BaseModel):
    input: str = Field(min_length=1)
    questions: list[dict[str, Any]] = Field(min_length=1, max_length=128)


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


@app.get("/api/models")
def get_models() -> dict[str, list[str]]:
    try:
        return {"models": list_chat_models()}
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except openai.OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"Models request failed: {exc}") from exc


@app.post("/api/chat")
def create_chat(payload: ChatRequest) -> StreamingResponse:
    try:
        chunks = stream_chat(
            model=payload.model,
            messages=[m.model_dump() for m in payload.messages],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    def generator():
        try:
            yield from chunks
        except openai.OpenAIError as exc:
            yield f"\n[upstream error] {exc}"

    return StreamingResponse(generator(), media_type="text/plain; charset=utf-8")


@app.post("/api/decisions")
def create_decisions(payload: DecisionsRequest) -> dict[str, Any]:
    try:
        return make_decisions(text=payload.input, questions=payload.questions)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except openai.OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"Decisions request failed: {exc}") from exc
