"""Code writer: generates complete, runnable code as a fenced markdown block."""

from app.agents.common import stream_markdown

NAME = "code_writer"
TASK = "generate_code"
SYSTEM = (
    "Write complete, runnable code for the request as one fenced markdown code block with a language tag, "
    "then at most two short sentences on how to run it. Default to Python if no language is given."
)


def handle(msg):
    return stream_markdown(msg, "return_code", SYSTEM)
