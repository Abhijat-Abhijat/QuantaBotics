"""HTTP API. POST /api/run streams orchestrator events as server-sent events."""

import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import config, orchestrator
from app.gemini import GeminiError

log = logging.getLogger("quantabotics")

app = FastAPI(title="QuantaBotics API", docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class RateLimiter:
    """Sliding one-minute window per client plus a global cap that protects the Gemini quota.

    ponytail: in-memory and per process; move to Redis if you run more than one instance.
    """

    def __init__(self, per_client: int, total: int, window: float = 60.0):
        self.per_client, self.total, self.window = per_client, total, window
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.all_hits: deque[float] = deque()

    def allow(self, client: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        for q in (self.hits[client], self.all_hits):
            while q and q[0] < cutoff:
                q.popleft()
        if len(self.hits[client]) >= self.per_client or len(self.all_hits) >= self.total:
            return False
        self.hits[client].append(now)
        self.all_hits.append(now)
        if len(self.hits) > 10_000:  # drop idle clients so memory stays bounded
            for key in [k for k, q in self.hits.items() if not q]:
                del self.hits[key]
        return True


limiter = RateLimiter(config.RATE_LIMIT_PER_IP, config.RATE_LIMIT_TOTAL)


class RunRequest(BaseModel):
    input: str = Field(min_length=1, max_length=config.MAX_INPUT_CHARS)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _events(user_input: str) -> AsyncIterator[str]:
    try:
        async for event in orchestrator.run(user_input):
            yield _sse(event)
    except (ValueError, GeminiError) as exc:
        yield _sse({"type": "error", "message": str(exc)})
    except Exception:
        log.exception("Pipeline failed")
        yield _sse({"type": "error", "message": "Something went wrong on the server. Try again."})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "gemini_configured": bool(config.GEMINI_API_KEY)}


@app.post("/api/run")
async def run(body: RunRequest, request: Request) -> StreamingResponse:
    client = request.client.host if request.client else "unknown"
    if not limiter.allow(client):
        raise HTTPException(status_code=429, detail="Too many requests. Wait a minute and try again.")
    return StreamingResponse(
        _events(body.input),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
