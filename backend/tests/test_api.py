import json

import pytest
from fastapi.testclient import TestClient

from app import gemini, main


@pytest.fixture
def client(monkeypatch):
    async def fake_stream(prompt, *, system, search=False, sources=None):
        if sources is not None:
            sources.append({"uri": "https://example.com", "title": "Example"})
        for part in ("Hello ", "**world**"):
            yield part

    monkeypatch.setattr(gemini, "stream_text", fake_stream)
    monkeypatch.setattr(main, "limiter", main.RateLimiter(per_client=100, total=100))
    return TestClient(main.app)


def events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


def test_streams_protocol_messages_chunks_and_result(client):
    got = events(client.post("/api/run", json={"input": "code: hello world"}))
    hops = [(e["message"]["sender"], e["message"]["receiver"], e["message"]["metadata"]["step"]) for e in got if e["type"] == "message"]
    assert hops == [("router", "code_writer", 1), ("code_writer", "orchestrator", 2)]
    assert "".join(e["text"] for e in got if e["type"] == "chunk") == "Hello **world**"
    assert got[-1] == {"type": "result", "agent": "code_writer", "kind": "markdown", "value": "Hello **world**"}


def test_summarizer_hands_off_to_formatter(client):
    got = events(client.post("/api/run", json={"input": "summarize: some long text"}))
    hops = [(e["message"]["sender"], e["message"]["receiver"]) for e in got if e["type"] == "message"]
    assert hops == [("router", "summarizer"), ("summarizer", "formatter"), ("formatter", "orchestrator")]
    assert got[-1]["word_count"] == 2


def test_search_returns_sources(client):
    assert events(client.post("/api/run", json={"input": "search: news"}))[-1]["sources"] == [{"uri": "https://example.com", "title": "Example"}]


def test_calculator_needs_no_gemini(client):
    assert events(client.post("/api/run", json={"input": "5 * (2 + 3) ^ 2"}))[-1]["value"] == "125"


def test_user_errors_become_error_events(client):
    assert events(client.post("/api/run", json={"input": "code:"}))[-1] == {"type": "error", "message": "Add some text after the prefix."}
    assert events(client.post("/api/run", json={"input": "1 / 0"}))[-1]["type"] == "error"


def test_rejects_oversized_and_empty_input(client):
    assert client.post("/api/run", json={"input": ""}).status_code == 422
    assert client.post("/api/run", json={"input": "x" * (main.config.MAX_INPUT_CHARS + 1)}).status_code == 422


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main, "limiter", main.RateLimiter(per_client=2, total=100))
    codes = [client.post("/api/run", json={"input": "1 + 1"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
