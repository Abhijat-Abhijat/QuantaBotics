import { API_URL } from "./config.js";

// Yields each JSON payload of a server-sent-events stream.
export async function* sseEvents(stream) {
  const reader = stream.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop();
    for (const line of lines) if (line.startsWith("data:")) yield JSON.parse(line.slice(5));
  }
  if (buffer.startsWith("data:")) yield JSON.parse(buffer.slice(5));
}

// Runs the agent pipeline on the backend and yields its events: message, chunk, result, error.
export async function* runPipeline(input) {
  let res;
  try {
    res = await fetch(`${API_URL}/api/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input }),
    });
  } catch {
    throw new Error("Can't reach the QuantaBotics server. Check your connection and try again.");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : `The server rejected the request (${res.status}).`);
  }
  yield* sseEvents(res.body);
}
