"""FastAPI 서버 — 회의 진행 과정을 SSE(Server-Sent Events)로 실시간 스트리밍한다."""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse

load_dotenv()

from .meeting import run_meeting  # noqa: E402  (load_dotenv 이후에 import)

app = FastAPI(title="AI 부서 회의")

_STATIC = Path(__file__).parent / "static"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/api/meeting")
async def meeting(topic: str) -> StreamingResponse:
    """주제를 받아 회의를 진행하고 이벤트를 SSE 로 흘려보낸다."""

    async def event_stream():
        topic_clean = (topic or "").strip()
        if not topic_clean:
            yield _sse({"type": "error", "message": "주제를 입력해주세요."})
            return
        async for event in run_meeting(topic_clean):
            yield _sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 등에서 버퍼링 방지
        },
    )


def _sse(data: dict) -> str:
    """dict 를 SSE data 프레임 문자열로 변환."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
