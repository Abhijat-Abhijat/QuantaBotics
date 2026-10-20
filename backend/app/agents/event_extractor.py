"""Event extractor: pulls out events and when they happen."""

from pydantic import BaseModel

from app import gemini
from app.protocol import reply, result

NAME = "event_extractor"
TASK = "extract_events"


class Event(BaseModel):
    event: str
    time: str


async def handle(msg):
    value = await gemini.generate_json(
        msg.content,
        system='List every event in the text with its time or date. Use "unknown" when no time is given.',
        schema=list[Event],
    )
    yield reply(msg, "return_events", result("json", value))
