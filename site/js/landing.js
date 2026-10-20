import { AGENTS, route } from "./agents.js";

const input = document.getElementById("routerInput");
const tryLink = document.getElementById("tryLink");
const board = document.getElementById("switchboard");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

// Switchboard: one wire from "you" to every agent; the routed wire lights up.
const SVG = "http://www.w3.org/2000/svg";
const svg = (tag, attrs) => {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};
const wires = {};
const nodes = {};
const src = { x: 46, y: 240 };
board.append(svg("circle", { cx: src.x, cy: src.y, r: 26, class: "src" }));
board.append(Object.assign(svg("text", { x: src.x, y: src.y + 5, class: "src-label", "text-anchor": "middle" }), { textContent: "you" }));
AGENTS.forEach((agent, i) => {
  const y = 32 + i * 52;
  const x = 280;
  wires[agent.id] = svg("path", { d: `M${src.x + 26},${src.y} C170,${src.y} 170,${y} ${x - 10},${y}`, class: "wire" });
  board.prepend(wires[agent.id]);
  const g = svg("g", { class: "node" });
  g.append(svg("circle", { cx: x, cy: y, r: 7 }));
  g.append(Object.assign(svg("text", { x: x + 18, y: y + 5 }), { textContent: agent.name }));
  nodes[agent.id] = g;
  board.append(g);
});

let active;
function update() {
  const value = input.value.trim();
  const { agent } = route(value);
  document.getElementById("routeName").textContent = value ? agent.name : "";
  document.getElementById("routeDesc").textContent = value ? agent.description : "";
  tryLink.href = value ? `chat.html?q=${encodeURIComponent(value)}` : "chat.html";
  const next = value ? agent.id : null;
  if (next === active) return;
  if (active) wires[active].classList.remove("active"), nodes[active].classList.remove("active");
  if (next) wires[next].classList.add("active"), nodes[next].classList.add("active");
  active = next;
}

// Demo typing cycles through examples until the visitor interacts with the input.
let demo = !reducedMotion;
const stopDemo = () => (demo = false);
input.addEventListener("focus", stopDemo);
input.addEventListener("pointerdown", stopDemo);
input.addEventListener("input", update);

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
async function typeDemo() {
  const examples = AGENTS.map((a) => a.example).filter((e) => !e.includes("<"));
  for (let i = 1; demo; i = (i + 1) % examples.length) {
    await wait(2200);
    while (demo && input.value) (input.value = input.value.slice(0, -1)), update(), await wait(18);
    for (const ch of examples[i]) {
      if (!demo) return;
      input.value += ch;
      update();
      await wait(45);
    }
  }
}

update();
typeDemo();

const rows = document.getElementById("agentRows");
for (const agent of AGENTS) {
  const prefix = document.createElement("code");
  prefix.textContent = agent.prefix ?? agent.hint;

  const example = document.createElement("button");
  example.type = "button";
  example.className = "example";
  example.textContent = agent.example;
  example.addEventListener("click", () => {
    input.value = agent.example;
    update();
    input.scrollIntoView({ block: "center" });
    input.focus();
  });

  const cells = [prefix, agent.name, [agent.description, example]].map((content) => {
    const td = document.createElement("td");
    td.append(...[content].flat());
    return td;
  });
  const tr = document.createElement("tr");
  tr.append(...cells);
  rows.append(tr);
}
