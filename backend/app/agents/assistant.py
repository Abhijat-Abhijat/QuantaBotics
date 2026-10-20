"""Assistant: default agent for anything without a prefix."""

from app.agents.common import stream_markdown

NAME = "assistant"
TASK = "answer"
SYSTEM = (
    "You are QuantaBotics, a concise and helpful assistant. Use markdown, "
    "and put any code in fenced code blocks with a language tag."
)


def handle(msg):
    return stream_markdown(msg, "return_answer", SYSTEM)
