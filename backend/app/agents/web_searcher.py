"""Web searcher: answers from live Google Search results and returns the sources."""

from app.agents.common import stream_markdown

NAME = "web_searcher"
TASK = "search_web"
SYSTEM = "Answer using current web results. Be concise and factual. Use markdown."


def handle(msg):
    return stream_markdown(msg, "return_search", SYSTEM, search=True)
