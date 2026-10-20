// Agent catalog and router for the landing page preview and chat labels.
// The backend router (backend/app/orchestrator.py) is the source of truth; tests/routing_cases.json keeps both in sync.

export const AGENTS = [
  { id: "code_writer", name: "Code writer", prefix: "code:", description: "Writes complete, runnable code.", example: "code: binary search in Python" },
  { id: "web_searcher", name: "Web searcher", prefix: "search:", description: "Answers from live Google Search results, with sources.", example: "search: latest Mars mission news" },
  { id: "summarizer", name: "Summarizer", prefix: "summarize:", description: "Condenses text, then hands it to the formatter agent.", example: "summarize: <paste an article>" },
  { id: "sentiment_analyzer", name: "Sentiment analyzer", prefix: "sentiment:", description: "Labels the tone of a text with a confidence score.", example: "sentiment: I love how fast this is" },
  { id: "event_extractor", name: "Event extractor", prefix: "events:", description: "Pulls out events and when they happen.", example: "events: The launch is on May 3, the review a week later." },
  { id: "keyword_extractor", name: "Keyword extractor", prefix: "keywords:", description: "Finds the five terms that matter most.", example: "keywords: <paste a paragraph>" },
  { id: "data_visualizer", name: "Data visualizer", prefix: "visualize:", description: "Turns numbers into a bar chart. JSON or plain words both work.", example: 'visualize: {"Q1": 120, "Q2": 180, "Q3": 90}' },
  { id: "calculator", name: "Calculator", prefix: null, hint: "2 + 2", description: "Solves arithmetic on the server, no AI call.", example: "5 * (2 + 3) ^ 2" },
  { id: "assistant", name: "Assistant", prefix: null, hint: "anything", description: "Answers anything else.", example: "Explain how transformers work" },
];

export const agentById = Object.fromEntries(AGENTS.map((a) => [a.id, a]));
const MATH = /^[\d\s.+\-*/%^()]+$/;

export function route(input) {
  const trimmed = input.trim();
  const lower = trimmed.toLowerCase();
  const agent = AGENTS.find((a) => a.prefix && lower.startsWith(a.prefix));
  if (agent) return { agent, text: trimmed.slice(agent.prefix.length).trim() };
  if (MATH.test(trimmed) && /\d/.test(trimmed)) return { agent: agentById.calculator, text: trimmed };
  return { agent: agentById.assistant, text: trimmed };
}
