"""Keyword extractor: finds the five terms that matter most."""

from app import gemini
from app.protocol import reply, result

NAME = "keyword_extractor"
TASK = "extract_keywords"


async def handle(msg):
    value = await gemini.generate_json(msg.content, system="Return the 5 most important keywords or key phrases in the text.", schema=list[str])
    yield reply(msg, "return_keywords", result("json", value))
