"""Runtime settings, read once from environment variables (see backend/.env.example)."""

import os


def _list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
# low, medium or high (some models also accept minimal). Lower is faster; empty uses the model default.
GEMINI_THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "low").strip().upper()
ALLOWED_ORIGINS = _list("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "8000"))
RATE_LIMIT_PER_IP = int(os.getenv("RATE_LIMIT_PER_IP", "20"))  # requests per minute per client
RATE_LIMIT_TOTAL = int(os.getenv("RATE_LIMIT_TOTAL", "200"))  # requests per minute across all clients
