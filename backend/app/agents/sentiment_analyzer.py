"""Sentiment analyzer: labels the tone of a text with a confidence score."""

from typing import Literal

from pydantic import BaseModel

from app import gemini
from app.protocol import reply, result

NAME = "sentiment_analyzer"
TASK = "analyze_sentiment"


class Sentiment(BaseModel):
    label: Literal["positive", "negative", "neutral", "mixed"]
    score: float
    reason: str


async def handle(msg):
    value = await gemini.generate_json(msg.content, system="Classify the sentiment of the text. score is confidence from 0 to 1.", schema=Sentiment)
    yield reply(msg, "return_sentiment", result("json", value))
