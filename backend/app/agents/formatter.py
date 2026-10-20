"""Formatter: second hop after the summarizer. Adds word count and returns to the orchestrator."""

from app.protocol import reply, result

NAME = "formatter"
TASK = "format_summary"


async def handle(msg):
    summary = msg.content["value"]
    yield reply(msg, "return_summary", result("markdown", summary, word_count=len(summary.split())))
