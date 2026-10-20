"""Router and orchestrator.

The router turns user input into the first Message. The orchestrator then delivers each Message to its
receiver until an agent replies to the orchestrator, emitting every hop plus streamed text as events.
"""

import re
from collections.abc import AsyncIterator

from app.agents import (
    assistant,
    calculator,
    code_writer,
    data_visualizer,
    event_extractor,
    formatter,
    keyword_extractor,
    sentiment_analyzer,
    summarizer,
    web_searcher,
)
from app.protocol import ORCHESTRATOR, ROUTER, Message, make_msg

AGENTS = {
    agent.NAME: agent
    for agent in (
        code_writer,
        web_searcher,
        summarizer,
        formatter,
        sentiment_analyzer,
        event_extractor,
        keyword_extractor,
        data_visualizer,
        calculator,
        assistant,
    )
}

PREFIXES = {
    "code:": code_writer,
    "search:": web_searcher,
    "summarize:": summarizer,
    "sentiment:": sentiment_analyzer,
    "events:": event_extractor,
    "keywords:": keyword_extractor,
    "visualize:": data_visualizer,
}
_MATH = re.compile(r"^[\d\s.+\-*/%^()]+$")
MAX_HOPS = 5


def route(user_input: str) -> tuple[str, str]:
    """Return (agent name, text for the agent). Prefix match is case-insensitive; text keeps its casing."""
    text = user_input.strip()
    lower = text.lower()
    for prefix, agent in PREFIXES.items():
        if lower.startswith(prefix):
            return agent.NAME, text[len(prefix):].strip()
    if _MATH.match(text) and any(ch.isdigit() for ch in text):
        return calculator.NAME, text
    return assistant.NAME, text


def _event(message: Message) -> dict:
    return {"type": "message", "message": message.model_dump()}


async def run(user_input: str) -> AsyncIterator[dict]:
    """Yield events: {"type": "message"} per hop, {"type": "chunk"} per text delta, then {"type": "result"}."""
    name, text = route(user_input)
    if not text:
        raise ValueError("Add some text after the prefix.")

    msg = make_msg(ROUTER, name, AGENTS[name].TASK, text, step=1)
    yield _event(msg)

    for _ in range(MAX_HOPS):
        answer: Message | None = None
        async for item in AGENTS[msg.receiver].handle(msg):
            if isinstance(item, Message):
                answer = item
            else:
                yield {"type": "chunk", "text": item}
        if answer is None:
            raise RuntimeError(f"Agent {msg.receiver} returned no message.")
        yield _event(answer)
        if answer.receiver == ORCHESTRATOR:
            yield {"type": "result", "agent": name, **answer.content}
            return
        if answer.receiver not in AGENTS:
            raise RuntimeError(f"Agent {answer.sender} addressed unknown agent {answer.receiver}.")
        msg = answer
    raise RuntimeError("Message exceeded the hop limit.")
