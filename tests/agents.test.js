import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { route } from "../site/js/agents.js";
import { sseEvents } from "../site/js/api.js";
import { renderMarkdown } from "../site/js/markdown.js";

const cases = JSON.parse(readFileSync(new URL("./routing_cases.json", import.meta.url), "utf8"));

test("route matches the shared cases the Python router is tested against", () => {
  for (const c of cases) {
    const { agent, text } = route(c.input);
    assert.deepEqual([agent.id, text], [c.agent, c.text], c.input);
  }
});

test("renderMarkdown escapes HTML and only links http(s) URLs", () => {
  const html = renderMarkdown('<img src=x onerror=alert(1)> [a](javascript:alert(1)) [b](https://x.dev/?q="1")');
  assert.ok(!html.includes("<img"));
  assert.ok(!html.includes('href="javascript'));
  assert.ok(html.includes('href="https://x.dev/?q=&quot;1&quot;"'));
});

test("renderMarkdown renders fenced code, including an unclosed fence mid-stream", () => {
  const done = renderMarkdown("Here:\n```python\nprint('<hi>')\n```\nDone **now**");
  assert.ok(done.includes("<span>python</span>"));
  assert.ok(done.includes("print(&#39;&lt;hi&gt;&#39;)"));
  assert.ok(done.includes("<strong>now</strong>"));
  assert.ok(renderMarkdown("```js\nlet a = 1").includes("<code>let a = 1</code>"));
  assert.ok(renderMarkdown("- a\n- `b`").includes("<ul><li>a</li><li><code>b</code></li></ul>"));
});

test("sseEvents parses data lines split across chunks", async () => {
  const parts = ['data: {"n":1}\n\nda', 'ta: {"n":2}\r\n\r\n', 'data: {"n":3}'];
  const stream = new ReadableStream({
    start(c) {
      for (const p of parts) c.enqueue(new TextEncoder().encode(p));
      c.close();
    },
  });
  const seen = [];
  for await (const e of sseEvents(stream)) seen.push(e.n);
  assert.deepEqual(seen, [1, 2, 3]);
});
