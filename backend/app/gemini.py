"""Thin wrapper over the Google Gen AI SDK, so agents never touch the SDK directly."""

import json
from collections.abc import AsyncIterator
from typing import Any

from google import genai
from google.genai import errors, types

from app import config


class GeminiError(RuntimeError):
    """Upstream failure with a message that is safe to show to users."""


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise GeminiError("The server has no GEMINI_API_KEY configured.")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


async def stream_text(prompt: str, *, system: str, search: bool = False, sources: list[dict] | None = None) -> AsyncIterator[str]:
    """Yield text deltas. With search, grounding sources are appended to `sources`."""
    tools = [types.Tool(google_search=types.GoogleSearch())] if search else None
    cfg = types.GenerateContentConfig(system_instruction=system, tools=tools)
    got_text = False
    try:
        stream = await _get_client().aio.models.generate_content_stream(model=config.GEMINI_MODEL, contents=prompt, config=cfg)
        async for chunk in stream:
            if chunk.text:
                got_text = True
                yield chunk.text
            if sources is not None:
                for candidate in chunk.candidates or []:
                    for grounding in (candidate.grounding_metadata and candidate.grounding_metadata.grounding_chunks) or []:
                        if grounding.web and grounding.web.uri:
                            sources.append({"uri": grounding.web.uri, "title": grounding.web.title or grounding.web.uri})
    except errors.APIError as exc:
        raise GeminiError(f"Gemini request failed: {exc.message or exc.status}") from exc
    if not got_text:
        raise GeminiError("Gemini returned no answer. Rephrase the request and try again.")


async def generate_json(prompt: str, *, system: str, schema: Any) -> Any:
    """Return JSON-decoded output constrained to `schema` (a pydantic model or type such as list[str])."""
    cfg = types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json", response_schema=schema)
    try:
        response = await _get_client().aio.models.generate_content(model=config.GEMINI_MODEL, contents=prompt, config=cfg)
    except errors.APIError as exc:
        raise GeminiError(f"Gemini request failed: {exc.message or exc.status}") from exc
    if not response.text:
        raise GeminiError("Gemini returned no answer. Rephrase the request and try again.")
    return json.loads(response.text)
