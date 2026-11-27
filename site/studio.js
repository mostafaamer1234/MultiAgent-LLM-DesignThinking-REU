// ResearchLLM Studio. Prompts follow scripts/MarketResearch.py, scripts/Agent1Persona.py and
// scripts/Agent2Hypothesis.py. Calls go from this tab to OpenAI with the visitor's own key.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const store = { get: (k) => { try { return sessionStorage.getItem(k); } catch (_) { return null; } }, set: (k, v) => { try { sessionStorage.setItem(k, v); } catch (_) {} } };
  const COLORS = ["pink", "blue", "green"];
  let SAMPLE = null, board = "sample", MINE = JSON.parse(store.get("rllm-mine") || "null") || { brief: { topic: "", description: "", vision: "" } };
  let active = 0;

  // ---------- model calls ----------
  async function llm(prompt, json = false) {
    const key = store.get("rllm-key");
    if (!key) { openKey(); throw new Error("Add your OpenAI API key to run the agents."); }
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
      body: JSON.stringify({ model: store.get("rllm-model") || "gpt-4o", messages: [{ role: "user", content: prompt }], ...(json ? { response_format: { type: "json_object" } } : {}) }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((body.error && body.error.message) || `OpenAI returned ${res.status}.`);
    return body.choices[0].message.content;
  }

  const researchPrompt = (topic) => `You are an expert market research analyst with 15+ years of experience in analyzing markets across various industries.
Your task is to conduct comprehensive market research on the given topic and provide detailed insights.

Topic: ${topic}

Please conduct thorough market research and provide a comprehensive report including:

1. Executive Summary - Key findings and insights
2. Market Overview - Current state and dynamics
3. Market Size - Total addressable market and growth rates
4. Market Segments - Key customer segments with characteristics
5. Competitive Analysis - Major competitors and their positioning
6. Market Trends - Current and emerging trends
7. Opportunities - Potential market opportunities
8. Risks & Challenges - Key risks and barriers
9. Recommendations - Strategic recommendations

Answer as a JSON object with the keys executive_summary (string), market_overview (string), total_market_size (string), market_segments (list of strings), competitors (list of strings), market_trends (list of strings), opportunities (list of strings), risks_and_challenges (list of strings) and recommendations (list of strings).

Provide detailed, actionable insights based on current market data and trends. Be specific with numbers, percentages, and concrete examples where possible.`;

  const personaPrompt = (market) => `
You are a market research expert. Generate exactly 3 distinct customer personas based on the market research below, make sure they are the costumer most likely to need or purchase the product.

Market Research:
${market}

IMPORTANT: You MUST generate exactly 3 personas. Each persona should be completely different from the others. Go further in-depth in each point (goals, pain points, values, etc...), by explaining them in more detail.

Format each persona exactly like this:

PERSONA 1:
Name: [Full Name]
Age: [Age]
Gender: [Gender]
Location: [City, State, Urban/Suburban/Rural]
Job/Education: [Job title and education]
Goals:
• [Goal 1]
• [Goal 2]
• [Goal 3]
• [Goal 4]
Pain Points:
• [Pain point 1]
• [Pain point 2]
• [Pain point 3]
• [Pain point 4]
Values:
• [Value 1]
• [Value 2]
• [Value 3]
• [Value 4]
Preferred Shopping Methods:
• [Method 1]
• [Method 2]
• [Method 3]
• [Method 4]
Brand Preferences:
• [Preference 1]
• [Preference 2]
• [Preference 3]
• [Preference 4]`;

  const rolePrompt = (p, market, history, q) => `You are role-playing as the following customer persona:

${personaText(p)}

You are based on this market research:
${market}

You are not an AI, you are the customer ${p.Name}, respond the same way the human customer would based on the above context as if you are the customer answering, you are role-playing as the customer so we can know more about the customer. Don't ever mention you are an LLM. Respond conversationally to the user's questions, staying in character. Be honest about your needs, frustrations, and preferences.

Conversation history:
${history.map((t) => `User: ${t.q}\nPersona: ${t.a}`).join("\n")}

User: ${q}
Persona:`;

  const hypothesisPrompt = (d) => `
Based on the following multiple customer personas and their conversations, the market research (market_data), the business description of what it is (business_description), and the vision/goals of what the business wants to achieve or where it wants to be (business_vision), generate 3-5 specific hypotheses about what problems the users might have or what they could want.

Business Description: ${d.brief.description}
Business Vision/Goal: ${d.brief.vision}

Customer Personas:
${d.personas.map(personaText).join("\n\n")}

All Conversations:
${Object.entries(d.interviews).map(([n, ts]) => `${n}:\n${ts.map((t) => `User: ${t.q}\n${n}: ${t.a}`).join("\n")}`).join("\n\n")}

Market Research Context:
${marketText(d.market)}

Generate hypotheses in this format:
1. Hypothesis: [Specific, testable hypothesis about user behavior/needs]
2. Hypothesis: [Another specific hypothesis]
3. Hypothesis: [Another specific hypothesis]

Focus on:
- Common pain points across personas
- Unmet needs that appear in multiple conversations
- Behavioral patterns that emerge
- Preferences that could be leveraged
- Problems that could be solved for multiple user types
- Differences between persona segments
- Gaps in the related market that need to be satisfied
- Problems the user might not be aware of
- Possible hidden opportunities
- Doing something new that could help people
- Be really creative

Hypotheses:
`;

  const prototypePrompt = (d, h) => `
Given this specific hypothesis, recommend a concrete prototype or test to validate it.

Business Description: ${d.brief.description}
Business Vision/Goal: ${d.brief.vision}

Hypothesis: ${h}

Customer Personas:
${d.personas.map(personaText).join("\n\n")}

Market Research Context:
${marketText(d.market)}

Provide a detailed prototype recommendation including:
1. What to build/test
2. How to test it
3. What metrics to measure
4. How to interpret results
5. Timeline for testing
6. Which persona segments to focus on

Make it specific and actionable. Focus on quick, low-cost ways to validate the hypothesis.

Prototype Recommendation:
`;

  // ---------- parsing / formatting ----------
  const LISTS = ["Goals", "Pain Points", "Values", "Preferred Shopping Methods", "Brand Preferences"];
  function parsePersonas(text) {
    return text.split(/PERSONA\s*\d+\s*:?/i).map((b) => b.trim()).filter((b) => /Name\s*:/i.test(b)).slice(0, 3).map((block) => {
      const p = {}; let list = null;
      for (const raw of block.split(/\n/)) {
        const line = raw.replace(/\*\*/g, "").trim();
        if (!line) continue;
        const head = LISTS.find((k) => new RegExp(`^${k}\\s*:`, "i").test(line));
        if (head) { list = head; p[head] = []; const rest = line.split(":").slice(1).join(":").trim(); if (rest) p[head].push(rest); continue; }
        const bullet = line.match(/^[•\-*–]\s*(.+)$/) || line.match(/^\d+[.)]\s*(.+)$/);
        if (bullet && list) { p[list].push(bullet[1]); continue; }
        const kv = line.match(/^(Name|Age|Gender|Location|Job\/Education)\s*:\s*(.+)$/i);
        if (kv) { p[{ name: "Name", age: "Age", gender: "Gender", location: "Location", "job/education": "Job/Education" }[kv[1].toLowerCase()]] = kv[2]; list = null; }
      }
      return p;
    });
  }
  function personaText(p) {
    return [`Name: ${p.Name}`, `Age: ${p.Age}`, `Gender: ${p.Gender}`, `Location: ${p.Location}`, `Job/Education: ${p["Job/Education"]}`,
      ...LISTS.filter((k) => p[k] && p[k].length).map((k) => `${k}:\n${p[k].map((v) => `• ${v}`).join("\n")}`)].join("\n");
  }
  function marketText(m) {
    return Object.entries(m || {}).map(([k, v]) => `${k.replace(/_/g, " ")}: ${Array.isArray(v) ? v.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join("; ") : typeof v === "string" ? v : JSON.stringify(v)}`).join("\n");
  }
  const parseHyps = (t) => t.split(/\n?\s*\d+\.\s*\**Hypothesis\**:?\s*/i).map((s) => s.replace(/\*\*/g, "").trim()).filter((s) => s.length > 20).slice(0, 5);
  function md(text) {
    const out = []; let list = false;
    for (const raw of String(text).split(/\n/)) {
      const line = esc(raw.trim()).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
      if (!line) { if (list) { out.push("</ul>"); list = false; } continue; }
      const li = line.match(/^(?:[-•*]|\d+\.)\s+(.*)$/);
      if (li && /^[-•*]/.test(line)) { if (!list) { out.push("<ul>"); list = true; } out.push(`<li>${li[1]}</li>`); continue; }
      if (list) { out.push("</ul>"); list = false; }
      out.push(/^#+\s/.test(raw.trim()) ? `<p><b>${line.replace(/^#+\s*/, "")}</b></p>` : `<p>${line}</p>`);
    }
    if (list) out.push("</ul>");
    return out.join("");
  }

  // ---------- rendering ----------
  const data = () => (board === "sample" ? SAMPLE : MINE);
  const short = (t) => { const s = String(t).split(/(?<=[.:])\s/)[0]; return s.length > 170 ? s.slice(0, 167) + "…" : s; };
  const thinking = (msg) => `<div class="thinking">${esc(msg)}</div>`;

  function renderBrief() {
    const d = data();
    if (board === "sample") {
      $("brief").innerHTML = `<h3>${esc(d.topic)}</h3><span class="k">Who we are</span><p>${esc(d.business_description)}</p><span class="k">Where we want to be</span><p>${esc(d.business_vision)}</p>
        <p class="hint" style="margin-top:8px">A real run saved from the study's wildfire use case. Switch to "Your project" to run the agents on your own idea.</p>`;
      return;
    }
    const b = d.brief;
    $("brief").innerHTML = `<h3>Your idea</h3>
      <label for="b-topic">Product or market</label><textarea id="b-topic" rows="2" placeholder="e.g. A subscription app that plans healthy meals for night-shift nurses">${esc(b.topic)}</textarea>
      <label for="b-desc">What the business is</label><textarea id="b-desc" rows="2" placeholder="e.g. Two-person startup selling to hospitals">${esc(b.description)}</textarea>
      <label for="b-vis">What it wants to achieve</label><textarea id="b-vis" rows="2" placeholder="e.g. Be the default wellness benefit for shift workers">${esc(b.vision)}</textarea>
      <button class="marker big" id="run" type="button">Run the agents</button><p class="err" id="run-err"></p>`;
    $("run").onclick = runAll;
  }
  function renderMarket() {
    const m = data().market;
    if (!m) { $("market").innerHTML = board === "mine" ? '<p class="hint">The research agent writes its report here.</p>' : ""; return; }
    const list = (k, title) => (m[k] && m[k].length ? `<div class="note blue"><h3>${title}</h3>${Array.isArray(m[k]) ? `<ul>${m[k].slice(0, 3).map((x) => `<li>${esc(short(typeof x === "string" ? x : Object.values(x).join(": ")))}</li>`).join("")}</ul>` : `<p>${esc(m[k])}</p>`}</div>` : "");
    $("market").innerHTML = (m.executive_summary ? `<div class="note blue"><h3>In short</h3><p>${esc(m.executive_summary)}</p></div>` : "") + list("market_trends", "Trends") + list("opportunities", "Opportunities") + list("risks_and_challenges", "Risks");
  }
  function renderPersonas() {
    const ps = data().personas || [];
    if (!ps.length) { $("personas").innerHTML = board === "mine" ? '<p class="hint">Three customer personas appear here.</p>' : ""; return; }
    $("personas").innerHTML = ps.map((p, i) => `<div class="note persona ${COLORS[i % 3]} ${i === active ? "on" : ""}" data-i="${i}" role="button" tabindex="0" aria-pressed="${i === active}">
      <span class="face">${esc((p.Name || "?").split(" ").map((w) => w[0]).join("").slice(0, 2))}</span><h3>${esc(p.Name)}</h3>
      <div class="meta">${esc([p.Age, p.Location].filter(Boolean).join(" · "))}<br />${esc(p["Job/Education"] || "")}</div>
      <details><summary>Goals and pain points</summary><span class="k">Goals</span><ul>${(p.Goals || []).map((g) => `<li>${esc(g)}</li>`).join("")}</ul><span class="k">Pain points</span><ul>${(p["Pain Points"] || []).map((g) => `<li>${esc(g)}</li>`).join("")}</ul></details>
    </div>`).join("");
  }
  function renderChat() {
    const d = data(), p = (d.personas || [])[active];
    if (!p) { $("who").innerHTML = "No one to talk to yet"; $("msgs").innerHTML = '<div class="bubble sys">Personas appear after the agents run.</div>'; $("say-in").disabled = true; return; }
    $("say-in").disabled = false;
    $("who").innerHTML = `${esc(p.Name)}<small>Tap another persona to switch. Ask about needs, habits, money, anything.</small>`;
    const turns = (d.interviews || {})[p.Name] || [];
    $("msgs").innerHTML = turns.map((t) => `<div class="bubble q">${esc(t.q)}</div><div class="bubble a">${esc(t.a)}</div>`).join("") ||
      `<div class="bubble sys">Say hello to ${esc(p.Name.split(" ")[0])}.${store.get("rllm-key") ? "" : " Interviews need your API key."}</div>`;
    $("msgs").scrollTop = $("msgs").scrollHeight;
  }
  let selHyp = null;
  function renderHyps() {
    const hs = data().hypotheses || [];
    if (!hs.length) { $("hyps").innerHTML = board === "mine" ? '<p class="hint">Testable hypotheses appear here.</p>' : ""; return; }
    $("hyps").innerHTML = hs.map((h, i) => `<div class="note green hyp ${selHyp === i ? "on" : ""}" data-h="${i}" role="button" tabindex="0"><h3>Hypothesis ${i + 1}</h3><p>${esc(h)}</p><span class="go">Plan a test →</span></div>`).join("");
  }
  function renderProto() {
    const d = data(), hs = d.hypotheses || [];
    if (selHyp === null || !hs[selHyp]) { $("proto").innerHTML = '<p class="hint">Pick a hypothesis to get a quick, low-cost way to test it.</p>'; return; }
    const plan = (d.prototypes || {})[hs[selHyp]];
    $("proto").innerHTML = plan ? `<div class="note lilac"><h3>Testing hypothesis ${selHyp + 1}</h3>${md(plan)}</div>` : thinking("Drafting a prototype plan");
  }
  function renderAll() {
    document.querySelectorAll("[data-board]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.board === board)));
    renderBrief(); renderMarket(); renderPersonas(); renderChat(); renderHyps(); renderProto();
  }
  const saveMine = () => store.set("rllm-mine", JSON.stringify(MINE));

  // ---------- actions ----------
  async function runAll() {
    const b = MINE.brief;
    b.topic = $("b-topic").value.trim(); b.description = $("b-desc").value.trim(); b.vision = $("b-vis").value.trim();
    if (!b.topic) { $("run-err").textContent = "Describe the product or market first."; return; }
    if (!store.get("rllm-key")) { openKey(); return; }
    Object.assign(MINE, { market: null, personas: [], interviews: {}, hypotheses: [], prototypes: {} });
    selHyp = null; active = 0; saveMine(); renderAll();
    $("run").disabled = true;
    try {
      $("market").innerHTML = thinking("Researching the market");
      MINE.market = JSON.parse(await llm(researchPrompt(b.topic), true)); saveMine(); renderMarket();
      $("personas").innerHTML = thinking("Imagining three customers");
      MINE.personas = parsePersonas(await llm(personaPrompt(marketText(MINE.market))));
      if (!MINE.personas.length) throw new Error("The model's personas couldn't be read. Try running again.");
      saveMine(); renderPersonas(); renderChat();
      const opener = `What is the hardest part of dealing with ${b.topic} for you today, and what would you happily pay to fix?`;
      for (const p of MINE.personas) {
        $("msgs").insertAdjacentHTML("beforeend", `<div class="bubble q">${esc(opener)}</div><div class="bubble sys">${esc(p.Name)} is thinking…</div>`);
        const a = await llm(rolePrompt(p, marketText(MINE.market), [], opener));
        MINE.interviews[p.Name] = [{ q: opener, a: a.trim() }]; saveMine();
      }
      renderChat();
      $("hyps").innerHTML = thinking("Looking for patterns");
      MINE.hypotheses = parseHyps(await llm(hypothesisPrompt(MINE))); saveMine(); renderHyps(); renderProto();
    } catch (err) {
      const e = $("run-err"); if (e) e.textContent = err.message;
      renderMarket(); renderPersonas(); renderChat(); renderHyps();
    } finally { const r = $("run"); if (r) r.disabled = false; }
  }

  async function ask(q) {
    const d = data(), p = (d.personas || [])[active];
    if (!p || !q.trim()) return;
    if (!store.get("rllm-key")) { openKey(); return; }
    d.interviews = d.interviews || {};
    const turns = d.interviews[p.Name] = d.interviews[p.Name] || [];
    $("msgs").insertAdjacentHTML("beforeend", `<div class="bubble q">${esc(q)}</div><div class="bubble sys" id="typing">${esc(p.Name.split(" ")[0])} is typing…</div>`);
    $("msgs").scrollTop = $("msgs").scrollHeight;
    try {
      const a = await llm(rolePrompt(p, board === "sample" ? marketText(SAMPLE.market) : marketText(MINE.market), turns, q));
      turns.push({ q, a: a.trim() });
      if (board === "mine") saveMine();
    } catch (err) { turns.push({ q, a: `(${err.message})` }); }
    renderChat();
  }

  async function plan(i) {
    selHyp = i; renderHyps();
    const d = data(), h = d.hypotheses[i];
    d.prototypes = d.prototypes || {};
    if (d.prototypes[h]) return renderProto();
    if (!store.get("rllm-key")) { $("proto").innerHTML = '<p class="hint">Prototype plans need your API key. Add one with "API key" at the top.</p>'; return; }
    renderProto();
    try { d.prototypes[h] = await llm(prototypePrompt(d, h)); if (board === "mine") saveMine(); }
    catch (err) { $("proto").innerHTML = `<p class="err">${esc(err.message)}</p>`; return; }
    if (selHyp === i) renderProto();
  }

  // ---------- key dialog ----------
  function openKey() { $("key").value = store.get("rllm-key") || ""; $("model").value = store.get("rllm-model") || "gpt-4o"; $("key-dlg").showModal(); }
  $("key-btn").addEventListener("click", openKey);
  $("key-save").addEventListener("click", () => { store.set("rllm-key", $("key").value.trim()); store.set("rllm-model", $("model").value.trim() || "gpt-4o"); setTimeout(renderChat); });

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-board]");
    if (b) { board = b.dataset.board; selHyp = null; active = 0; renderAll(); return; }
    const p = e.target.closest(".persona[data-i]");
    if (p && !e.target.closest("summary")) { active = +p.dataset.i; renderPersonas(); renderChat(); return; }
    const h = e.target.closest(".hyp[data-h]");
    if (h) plan(+h.dataset.h);
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.matches(".persona, .hyp")) e.target.click(); });
  $("say").addEventListener("submit", (e) => { e.preventDefault(); const q = $("say-in").value; $("say-in").value = ""; ask(q); });

  fetch("sample.json").then((r) => r.json()).then((s) => {
    SAMPLE = s;
    selHyp = 0;
    renderAll();
  });
})();
