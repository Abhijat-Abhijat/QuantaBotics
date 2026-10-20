import { agentById } from "./agents.js";
import { runPipeline } from "./api.js";
import { renderMarkdown } from "./markdown.js";

const $ = (id) => document.getElementById(id);
const thread = $("thread");
const input = $("input");
const sendBtn = $("send");
let lastOutput = "";

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function scrollToEnd() {
  thread.scrollTop = thread.scrollHeight;
}

function addMessage(text, className) {
  const node = el("div", `msg ${className}`, text);
  thread.append(node);
  scrollToEnd();
  return node;
}

// renderMarkdown escapes all input and emits only its own tags, so innerHTML is safe here.
function markdownNode(text, className = "md") {
  const node = el("div", className);
  node.innerHTML = renderMarkdown(text);
  return node;
}

// One protocol hop: "sender → receiver · task", expandable to the full message JSON.
function hopNode(message) {
  const details = el("details", "msg trace");
  details.append(el("summary", "", `${message.sender} → ${message.receiver} · ${message.task}`), el("pre", "", JSON.stringify(message, null, 2)));
  return details;
}

function asText({ kind, value }) {
  if (kind === "chart") return value.map((r) => `${r.label}: ${r.value}`).join("\n");
  if (kind === "json") return JSON.stringify(value, null, 2);
  return value;
}

function renderChart(rows) {
  const max = Math.max(...rows.map((r) => Math.abs(r.value))) || 1;
  const wrap = el("div", "bars");
  wrap.setAttribute("role", "img");
  wrap.setAttribute("aria-label", `Bar chart: ${rows.map((r) => `${r.label} ${r.value}`).join(", ")}`);
  for (const { label, value } of rows) {
    const fill = el("div", "fill");
    fill.style.width = `${(Math.abs(value) / max) * 100}%`; // ponytail: negatives drawn by magnitude; add a zero axis if needed
    const track = el("div", "track");
    track.append(fill);
    const row = el("div", "bar");
    row.append(el("span", "label", label), track, el("span", "num", value.toLocaleString()));
    wrap.append(row);
  }
  return wrap;
}

function renderSources(sources) {
  const box = el("div", "sources", "Sources");
  const list = el("ol");
  for (const { uri, title } of sources) {
    if (!/^https?:\/\//.test(uri ?? "")) continue;
    const a = el("a", "", title || uri);
    a.href = uri;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    const li = el("li");
    li.append(a);
    list.append(li);
  }
  box.append(list);
  return box;
}

function renderResult(result) {
  lastOutput = asText(result);
  const name = (agentById[result.agent]?.name ?? result.agent).toLowerCase();
  $("resultTitle").textContent = result.word_count ? `{ ${name} · ${result.word_count} words }` : `{ ${name} }`;
  const view =
    result.kind === "chart" ? renderChart(result.value) : result.kind === "markdown" ? markdownNode(lastOutput) : el("pre", "", lastOutput);
  $("resultBody").replaceChildren(view);
  if (result.sources?.length) $("resultBody").append(renderSources(result.sources));
}

async function send() {
  const value = input.value.trim();
  if (!value || sendBtn.disabled) return;

  addMessage(value, "user");
  input.value = "";
  const pending = addMessage("", "bot pending");
  pending.setAttribute("aria-label", "Working");
  pending.append(el("span"));
  sendBtn.disabled = true;

  // Streamed text replaces the typing dots; rendering is batched to one paint per frame.
  let bubble = null;
  let streamed = "";
  let frame = 0;
  let result = null;
  const paint = () => {
    frame = 0;
    const atBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight < 40;
    bubble.innerHTML = renderMarkdown(streamed);
    if (atBottom) scrollToEnd();
  };

  try {
    for await (const event of runPipeline(value)) {
      if (event.type === "message") {
        // Hops before any text sit above the reply; later hops (agent → orchestrator) follow it.
        if (bubble) thread.append(hopNode(event.message));
        else pending.before(hopNode(event.message));
      } else if (event.type === "chunk") {
        streamed += event.text;
        if (!bubble) {
          bubble = el("div", "msg bot md streaming");
          pending.replaceWith(bubble);
        }
        frame ||= requestAnimationFrame(paint);
      } else if (event.type === "result") {
        result = event;
      } else if (event.type === "error") {
        throw new Error(event.message);
      }
    }
    if (!result) throw new Error("The server closed the connection before answering. Try again.");

    cancelAnimationFrame(frame);
    if (bubble) {
      bubble.classList.remove("streaming");
      streamed = result.value;
      paint();
    } else {
      pending.replaceWith(
        result.kind === "markdown"
          ? markdownNode(result.value, "msg bot md")
          : el("div", "msg bot", result.kind === "chart" ? "Chart is ready in the output panel." : asText(result)),
      );
    }
    renderResult(result);
  } catch (err) {
    cancelAnimationFrame(frame);
    bubble?.classList.remove("streaming");
    pending.remove();
    addMessage(err.message, "bot error");
  } finally {
    sendBtn.disabled = false;
    scrollToEnd();
    input.focus();
  }
}

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  send();
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    send();
  }
});

async function copyWithFeedback(btn, text, done) {
  const idle = btn.textContent;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = done;
  } catch {
    btn.textContent = "Copy failed";
  }
  setTimeout(() => (btn.textContent = idle), 1500);
}

$("copy").addEventListener("click", (e) => lastOutput && copyWithFeedback(e.currentTarget, lastOutput, "✅"));

// Copy buttons inside rendered code blocks, in the thread and the output panel.
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".code-copy");
  if (btn) copyWithFeedback(btn, btn.closest(".code-block").querySelector("code").textContent, "Copied");
});

const prefill = new URLSearchParams(location.search).get("q");
if (prefill) input.value = prefill;
input.focus();
