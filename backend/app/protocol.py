"""Agent message protocol. Every hop between router, agents and orchestrator is one Message."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

ROUTER = "router"
ORCHESTRATOR = "orchestrator"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Metadata(BaseModel):
    step: int
    timestamp: str = Field(default_factory=_timestamp)


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    receiver: str
    task: str
    content: Any
    metadata: Metadata


def make_msg(sender: str, receiver: str, task: str, content: Any, step: int) -> Message:
    return Message(sender=sender, receiver=receiver, task=task, content=content, metadata=Metadata(step=step))


def reply(to: Message, task: str, content: Any, receiver: str = ORCHESTRATOR) -> Message:
    """Answer a message as its receiver. The default receiver ends the pipeline."""
    return make_msg(to.receiver, receiver, task, content, to.metadata.step + 1)


def result(kind: str, value: Any, **extra: Any) -> dict:
    """Final payload shape the frontend renders. kind is text, markdown, json or chart."""
    return {"kind": kind, "value": value, **extra}
