"""Helper for agents whose answer is streamed markdown from Gemini."""

from collections.abc import AsyncIterator

from app import gemini
from app.protocol import ORCHESTRATOR, Message, reply, result


async def stream_markdown(msg: Message, task: str, system: str, *, search: bool = False, receiver: str = ORCHESTRATOR) -> AsyncIterator[str | Message]:
    """Yield text deltas as they arrive, then the reply Message carrying the full answer."""
    parts: list[str] = []
    sources: list[dict] = []
    async for delta in gemini.stream_text(msg.content, system=system, search=search, sources=sources if search else None):
        parts.append(delta)
        yield delta
    extra = {"sources": sources} if sources else {}
    yield reply(msg, task, result("markdown", "".join(parts), **extra), receiver)
