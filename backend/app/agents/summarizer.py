"""Summarizer: condenses text, then hands the summary to the formatter agent."""

from app.agents import formatter
from app.agents.common import stream_markdown

NAME = "summarizer"
TASK = "summarize"
SYSTEM = "Summarize the text in 2 to 4 plain sentences."


def handle(msg):
    return stream_markdown(msg, formatter.TASK, SYSTEM, receiver=formatter.NAME)
