const METHODS = {
  "Single prompt": {
    desc: "One prompt, the model's own knowledge. Personas, hypotheses and prototype ideas come back in a single pass.",
    steps: [["Model knowledge", "No outside research"], ["One pass", "Personas, hypotheses and prototypes together", true]],
  },
  "Single prompt + web": {
    desc: "A web-search agent gathers market context first. The design-thinking output is still written in one pass.",
    steps: [["Web market research", "Search agent collects current signals"], ["One pass", "Personas, hypotheses and prototypes together", true]],
  },
  "Multi-agent + web": {
    desc: "Research, empathy and synthesis are separate agents. Personas are interviewed in role-play before any hypothesis is written.",
    steps: [["Web market research", "Search agent collects current signals"], ["Personas", "Grounded in the research"],
      ["Role-play interviews", "Each persona answers in character"], ["Hypotheses", "Testable, tied to interview findings"], ["Prototype direction", "What to build first to test them"]],
  },
};

const seg = document.getElementById("method");
seg.innerHTML = Object.keys(METHODS).map((m) => `<button aria-pressed="false">${m}</button>`).join("");
function show(name) {
  seg.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.textContent === name)));
  document.getElementById("method-desc").textContent = METHODS[name].desc;
  document.getElementById("flow").innerHTML = METHODS[name].steps.map(([t, s, merged], i) =>
    `<li class="${merged ? "merged" : ""}" style="animation-delay:${i * 70}ms"><em>${String(i + 1).padStart(2, "0")}</em><b>${t}</b><span>${s}</span></li>`).join("");
}
seg.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => show(b.textContent)));
show("Multi-agent + web");
