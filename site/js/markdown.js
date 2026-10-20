// Minimal markdown to HTML. Escapes everything first, then adds only known tags, so model output can't inject markup.
// ponytail: no tables, blockquotes or nested lists; swap in marked + DOMPurify if replies need them.

const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function inline(text) {
  return text
    .split(/(`[^`\n]+`)/)
    .map((part, i) => {
      if (i % 2) return `<code>${esc(part.slice(1, -1))}</code>`;
      return esc(part)
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
        .replace(/\*\*(?=\S)(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*(?=\S)([^*]+?)\*/g, "$1<em>$2</em>");
    })
    .join("");
}

const FENCE = /^\s*```\s*([\w+#.-]*)\s*$/;
const BULLET = /^\s*[-*+]\s+(.*)/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)/;
const HEADING = /^(#{1,6})\s+(.*)/;

function codeBlock(code, lang) {
  return `<div class="code-block"><div class="code-head"><span>${esc(lang || "code")}</span><button type="button" class="code-copy">Copy</button></div><pre><code>${esc(code)}</code></pre></div>`;
}

export function renderMarkdown(src) {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const out = [];
  let i = 0;

  const list = (pattern, tag) => {
    const items = [];
    while (i < lines.length && pattern.test(lines[i])) items.push(`<li>${inline(lines[i++].match(pattern)[1])}</li>`);
    out.push(`<${tag}>${items.join("")}</${tag}>`);
  };

  while (i < lines.length) {
    const line = lines[i];
    const fence = line.match(FENCE);
    const heading = line.match(HEADING);

    if (fence) {
      const body = [];
      i++;
      while (i < lines.length && !/^\s*```\s*$/.test(lines[i])) body.push(lines[i++]);
      i++; // closing fence; while streaming it may not exist yet
      out.push(codeBlock(body.join("\n"), fence[1]));
    } else if (heading) {
      const level = Math.min(heading[1].length + 2, 6);
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      i++;
    } else if (BULLET.test(line)) {
      list(BULLET, "ul");
    } else if (NUMBERED.test(line)) {
      list(NUMBERED, "ol");
    } else if (!line.trim()) {
      i++;
    } else {
      const para = [];
      while (i < lines.length && lines[i].trim() && ![FENCE, HEADING, BULLET, NUMBERED].some((re) => re.test(lines[i]))) {
        para.push(inline(lines[i++]));
      }
      out.push(`<p>${para.join("<br>")}</p>`);
    }
  }
  return out.join("");
}
