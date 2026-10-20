"""Data visualizer: turns label/number pairs into chart rows. Parses locally, asks Gemini only for plain text."""

import ast
import json
import math

from pydantic import BaseModel

from app import gemini
from app.protocol import reply, result

NAME = "data_visualizer"
TASK = "generate_chart_data"


class Point(BaseModel):
    label: str
    value: float


def parse_chart_data(text: str) -> list[dict] | None:
    """Accept a JSON object or Python dict literal of numbers; return None for anything else."""
    for parse in (json.loads, ast.literal_eval):
        try:
            data = parse(text)
            break
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            continue
    else:
        return None
    if not isinstance(data, dict) or not data:
        return None
    rows = []
    for label, value in data.items():
        if isinstance(value, bool):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        rows.append({"label": str(label), "value": number})
    return rows


async def handle(msg):
    rows = parse_chart_data(msg.content)
    if rows is None:
        rows = await gemini.generate_json(msg.content, system="Extract label and numeric value pairs to chart from the text.", schema=list[Point])
    if not rows:
        raise ValueError('No numbers found to chart. Try: visualize: {"A": 10, "B": 20}')
    yield reply(msg, "return_visualization_data", result("chart", rows))
