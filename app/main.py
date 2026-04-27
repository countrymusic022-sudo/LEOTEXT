from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from app.srt_utils import segments_to_srt

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".mov"}

app = FastAPI(title="語音/影片轉字幕工具")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

client = OpenAI()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="只支援 mp3, wav, m4a, mp4, mov")

    file_id = uuid.uuid4().hex
    upload_path = UPLOAD_DIR / f"{file_id}{suffix}"
    srt_path = OUTPUT_DIR / f"{file_id}.srt"

    with upload_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        with upload_path.open("rb") as media_file:
            transcription = client.audio.transcriptions.create(
                file=media_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = getattr(transcription, "segments", None) or transcription.get("segments", [])
        if not segments:
            raise HTTPException(status_code=500, detail="轉錄結果沒有 segments")

        srt_text = segments_to_srt(segments)
        srt_path.write_text(srt_text, encoding="utf-8")

        return {
            "message": "轉換完成",
            "filename": srt_path.name,
            "download_url": f"/api/download/{srt_path.name}",
            "preview": srt_text,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"轉換失敗: {exc}") from exc


@app.get("/api/download/{filename}")
def download_srt(filename: str) -> FileResponse:
    target = OUTPUT_DIR / filename
    if not target.exists() or target.suffix.lower() != ".srt":
        raise HTTPException(status_code=404, detail="SRT 不存在")
    return FileResponse(target, media_type="application/x-subrip", filename=filename)
