# QuantaBotics

One chat box, nine specialist AI agents. A Python orchestrator routes each message to the agent that fits, agents pass protocol messages to each other, and every hop plus the answer streams back to the browser as it happens. Agents run on Google Gemini.

- **Frontend:** static site in `site/`, deployed to GitHub Pages.
- **Backend:** FastAPI app in `backend/`, deployed to any host that runs Docker (Render blueprint included). It holds the Gemini API key.

## Agents

| Input                              | Agent              | Runs on                          |
| ---------------------------------- | ------------------ | -------------------------------- |
| `code: binary search in Python`    | Code writer        | Gemini, streamed                 |
| `search: latest Mars mission news` | Web searcher       | Gemini + Google Search, streamed |
| `summarize: <long text>`           | Summarizer → Formatter | Gemini, streamed, then a second hop adds word count |
| `sentiment: I love it`             | Sentiment analyzer | Gemini structured JSON           |
| `events: <text>`                   | Event extractor    | Gemini structured JSON           |
| `keywords: <text>`                 | Keyword extractor  | Gemini structured JSON           |
| `visualize: {"A": 10, "B": 20}`    | Data visualizer    | Python; Gemini only for plain-text data |
| `5 * (2 + 3) ^ 2`                  | Calculator         | Python AST evaluator, no AI call |
| anything else                      | Assistant          | Gemini, streamed                 |

## Message protocol

Every hop is a `Message` (`backend/app/protocol.py`):

```json
{
  "id": "9f5fec0a-a5fe-44ec-8ed8-1d51fdf0e81a",
  "sender": "router",
  "receiver": "summarizer",
  "task": "summarize",
  "content": "text to summarize",
  "metadata": { "step": 1, "timestamp": "2026-10-20T12:18:25Z" }
}
```

The router creates the first message. The orchestrator (`backend/app/orchestrator.py`) delivers each message to its receiver until an agent replies to `orchestrator`. An agent can forward to another agent instead, as the summarizer does to the formatter.

`POST /api/run` with `{"input": "..."}` returns server-sent events, one JSON object per `data:` line:

| `type`    | Payload                                                     |
| --------- | ----------------------------------------------------------- |
| `message` | `message`: one protocol hop                                 |
| `chunk`   | `text`: streamed text delta                                 |
| `result`  | `agent`, `kind` (`text`, `markdown`, `json`, `chart`), `value`, optional `sources`, `word_count` |
| `error`   | `message`: safe to show to users                            |

Interactive API docs are served at `/api/docs`.

## Project structure

```
backend/
  app/
    main.py            FastAPI app: /api/run (SSE), /api/health, CORS, rate limit
    orchestrator.py    Router and hop loop
    protocol.py        Message, make_msg, reply
    gemini.py          Google Gen AI SDK wrapper
    config.py          Settings from environment variables
    agents/            One module per agent (NAME, TASK, handle)
  tests/               pytest: router, calculator safety, chart parsing, API stream
  Dockerfile
  requirements.txt, requirements-dev.txt
  .env.example
site/                  GitHub Pages frontend
  index.html, chat.html
  css/styles.css
  js/config.js         Backend URL (rewritten at deploy)
  js/api.js            SSE client for /api/run
  js/chat.js, js/landing.js, js/markdown.js, js/agents.js
tests/                 Node tests for the frontend
  routing_cases.json   Shared cases both routers are tested against
render.yaml            Render blueprint for the backend
.github/workflows/pages.yml  Test both, then deploy site/ to GitHub Pages
```

## Run locally

Backend (Python 3.11+):

```sh
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env, then set GEMINI_API_KEY
uvicorn app.main:app --reload --env-file .env
```

Frontend, in a second terminal from the repo root (Node 18+):

```sh
npm start        # http://localhost:3000, talks to http://localhost:8000
```

Tests:

```sh
npm test                          # frontend
cd backend && python -m pytest    # backend
```

## Deploy

### 1. Backend on Render

1. In Render, choose **New → Blueprint** and select this repo. It reads `render.yaml`.
2. Set `GEMINI_API_KEY` to your key from [Google AI Studio](https://aistudio.google.com/apikey).
3. Set `ALLOWED_ORIGINS` to your Pages origin, for example `https://<user>.github.io`.
4. Note the service URL, for example `https://quantabotics-api.onrender.com`.

Any Docker host works the same way (Cloud Run, Fly.io, Railway): build `backend/Dockerfile` and set the same variables. The free Render plan sleeps when idle, so the first request after a pause takes a few extra seconds.

### 2. Frontend on GitHub Pages

1. In the repo, open **Settings → Secrets and variables → Actions → Variables** and add `API_URL` with the backend URL.
2. Open **Settings → Pages** and set **Source** to **GitHub Actions**.
3. Push to `main`. The workflow runs both test suites, writes `API_URL` into the site, and publishes `site/`.

## Security

- The Gemini key lives only in the backend environment. Never commit `backend/.env`.
- CORS allows only `ALLOWED_ORIGINS`.
- Input is capped at `MAX_INPUT_CHARS`. Requests are limited per client (`RATE_LIMIT_PER_IP`) and in total (`RATE_LIMIT_TOTAL`) per minute; the total cap is what protects your Gemini quota. Limits are in memory, so use one instance or move them to Redis.
- The calculator walks the Python AST with an allowlist of operators instead of calling `eval`.
- Model output is rendered by an escape-first markdown renderer, and the pages ship a strict Content Security Policy.

## Add an agent

1. Create `backend/app/agents/<name>.py` with `NAME`, `TASK` and `handle(msg)`, an async generator that may yield text chunks and must yield one reply `Message` (use `reply()` and `result()` from `app.protocol`).
2. Register it in `AGENTS` and, if it has a prefix, `PREFIXES` in `backend/app/orchestrator.py`.
3. Add it to `AGENTS` in `site/js/agents.js` and a case to `tests/routing_cases.json`.

## Contact

- Email: [abhijat789@gmail.com](mailto:abhijat789@gmail.com)
- GitHub: [Abhijat-Abhijat](https://github.com/Abhijat-Abhijat)

## License

MIT