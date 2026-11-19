/* Expert console – analytics, knowledge-graph explorer, language teaching,
   learning audit, evaluation and photo-model report. */
(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const pct = (v) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
  let token = sessionStorage.getItem("expertToken") || "";
  let SYMPTOMS = [];

  async function api(path, body) {
    const headers = { "X-Expert-Token": token };
    const init = body ? { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body) } : { headers };
    const res = await fetch(path, init);
    if (res.status === 401 || res.status === 403) { $("#tokenBox").classList.remove("hidden"); throw new Error("locked"); }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }

  // ------------------------------------------------------------ overview
  async function overview() {
    const s = await api("/api/expert/stats");
    $("#unmatchedCount").textContent = s.unmatched_open || "";
    const fb = s.feedback || {};
    const max = Math.max(1, ...s.top_diseases.map((d) => d.n));
    const dmax = Math.max(1, ...s.daily.map((d) => d.n));
    $("#p-overview").innerHTML = `
      <h2>Overview</h2>
      <div class="kpis">
        <div class="kpi"><span>Consultations</span><b>${s.consultations}</b></div>
        <div class="kpi"><span>Farmer-confirmed accuracy</span><b>${pct(s.accuracy_feedback)}</b><small>${(fb.confirmed || 0)} confirmed · ${(fb.corrected || 0)} corrected · ${(fb.rejected || 0)} wrong</small></div>
        <div class="kpi"><span>Avg. follow-up questions</span><b>${s.avg_questions ?? "—"}</b></div>
        <div class="kpi"><span>Used a photo</span><b>${pct(s.photo_rate)}</b></div>
        <div class="kpi"><span>Phrases to teach</span><b>${s.unmatched_open}</b></div>
        <div class="kpi"><span>Knowledge graph</span><b>${s.kg.diseases}</b><small>diseases · ${s.kg.symptoms} symptoms · ${s.kg.layterms} lay-terms · ${s.kg.has_symptom_edges + s.kg.treated_by_edges} weighted edges</small></div>
      </div>
      <div class="grid2">
        <div class="card"><p class="eyebrow">Most diagnosed</p>
          ${s.top_diseases.map((d) => `<div class="hbar"><span>${esc(d.name_en)}</span><span class="track"><span class="fill" style="width:${(d.n / max) * 100}%"></span></span><span class="v">${d.n}</span></div>`).join("") || '<p class="muted">No consultations yet.</p>'}
        </div>
        <div class="card"><p class="eyebrow">Consultations — last 14 days</p>
          <div class="cols">${s.daily.map((d) => `<div title="${esc(d.day)}: ${d.n}"><i style="height:${(d.n / dmax) * 100}%"></i>${esc(d.day.slice(5))}</div>`).join("") || '<p class="muted">—</p>'}</div>
        </div>
      </div>
      <div class="card scroll"><p class="eyebrow">Recent consultations</p>
        <table class="ex"><thead><tr><th>When</th><th>Farmer said</th><th>Top</th><th class="num">P</th><th>Status</th><th class="num">Qs</th><th>Photo</th><th>Outcome</th></tr></thead><tbody>
        ${s.recent.map((r) => `<tr><td>${new Date(r.created_at * 1000).toLocaleString()}</td><td style="font-family:var(--font-ta)">${esc((r.input_text || "").slice(0, 80))}</td>
          <td>${esc(r.top_disease)}</td><td class="num">${r.top_prob != null ? Math.round(r.top_prob * 100) + "%" : ""}</td>
          <td><span class="pill ${esc(r.status)}">${esc(r.status)}</span></td><td class="num">${r.questions_asked}</td><td>${r.photo_used ? "✓" : ""}</td>
          <td>${esc(r.outcome || "")}${r.final_disease && r.outcome === "corrected" ? " → " + esc(r.final_disease) : ""}</td></tr>`).join("")}
        </tbody></table></div>`;
  }

  // ------------------------------------------------------------ graph
  let network = null, graphData = null;
  async function graph() {
    graphData = await api(`/api/expert/graph?layterms=${$("#showLayterms").checked ? 1 : 0}`);
    drawGraph();
  }
  function drawGraph() {
    const colors = { disease: "#c8432b", symptom: "#5c8f3a", treatment: "#b88a12", layterm: "#6f7fa8" };
    const showT = $("#showTreatments").checked;
    const th = document.documentElement.dataset.theme;
    const dark = th ? th === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    const nodes = graphData.nodes.filter((n) => showT || n.kind !== "treatment").map((n) => ({
      id: n.id, label: n.kind === "layterm" ? n.label : n.label.length > 34 ? n.label.slice(0, 32) + "…" : n.label,
      title: n.kind === "disease"
        ? `Disease: ${n.label}\nConfirmed: ${n.confirmed || 0} · Corrected: ${n.corrected || 0}`
        : n.kind === "symptom"
          ? `Symptom: ${n.label}${n.label_ta ? "\n" + n.label_ta : ""}`
          : n.kind === "treatment"
            ? `Treatment: ${n.label}`
            : `Lay-term: ${n.label}`,
      color: { background: colors[n.kind], border: colors[n.kind], highlight: { background: "#1f3a22", border: "#1f3a22" } },
      shape: n.kind === "disease" ? "dot" : n.kind === "treatment" ? "diamond" : n.kind === "layterm" ? "box" : "dot",
      size: n.kind === "disease" ? 22 : n.kind === "symptom" ? 11 : 9,
      font: { color: dark ? "#eef0e6" : "#1f2a1c", size: n.kind === "disease" ? 16 : 12, face: "Manrope, Noto Sans Tamil" },
    }));
    const ids = new Set(nodes.map((n) => n.id));
    const edges = graphData.edges.filter((e) => ids.has(e.from) && ids.has(e.to)).map((e) => ({
      from: e.from, to: e.to, width: 0.5 + e.weight * 4,
      title: e.rel === "HAS_SYMPTOM"
        ? `HAS_SYMPTOM | weight ${e.weight} | seed ${e.seed} | drift ${e.drift >= 0 ? "+" : ""}${e.drift}`
        : `${e.rel} · weight ${e.weight}`,
      color: { color: e.rel === "TREATED_BY" ? "#d9c27a" : e.rel === "LAYTERM_MAPS_TO" ? "#aab4d0" : "#9fbf86", opacity: 0.7 },
      arrows: { to: { enabled: true, scaleFactor: 0.4 } },
    }));
    const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
    if (network) {
      network.setData(data);
      return;
    }
    network = new vis.Network($("#graph"), data, {
      physics: { solver: "forceAtlas2Based", forceAtlas2Based: { gravitationalConstant: -60, springLength: 90 }, stabilization: { iterations: 250 } },
      interaction: { hover: true, tooltipDelay: 120 },
    });
    network.once("stabilizationIterationsDone", () => {
      network.setOptions({ physics: false });
    });
    network.on("click", (p) => { if (p.nodes.length) network.selectNodes([p.nodes[0], ...network.getConnectedNodes(p.nodes[0])]); });
  }

  // Full screen: the browser Fullscreen API on the graph + toolbar; where that is not
  // available (e.g. iPhone Safari) the same container is pinned over the page instead.
  const wrap = () => $("#graphWrap");
  const fsElement = () => document.fullscreenElement || document.webkitFullscreenElement;
  const isFull = () => fsElement() === wrap() || wrap().classList.contains("pseudo-full");
  function syncFullUi() {
    const on = isFull();
    wrap().classList.toggle("is-full", on);
    document.body.classList.toggle("graph-full", wrap().classList.contains("pseudo-full"));
    $("#graphFull").setAttribute("aria-pressed", String(on));
    $("#graphFull").title = on ? "Exit full screen (Esc)" : "Full screen (F)";
    $("#graphFullLabel").textContent = on ? "Exit full screen" : "Full screen";
    if (network) requestAnimationFrame(() => { network.setSize("100%", "100%"); network.redraw(); network.fit({ animation: { duration: 300 } }); });
  }
  async function toggleFull() {
    const el = wrap();
    if (isFull()) {
      if (fsElement()) await (document.exitFullscreen || document.webkitExitFullscreen).call(document);
      else el.classList.remove("pseudo-full");
    } else {
      const req = el.requestFullscreen || el.webkitRequestFullscreen;
      try { if (!req) throw new Error("no fullscreen api"); await req.call(el); } catch { el.classList.add("pseudo-full"); }
    }
    syncFullUi();
  }

  // ------------------------------------------------------------ outbreaks
  let obMap = null, obLayer = null;
  const PALETTE = ["#c8432b", "#2f5d34", "#b88a12", "#2f5d8a", "#7a3e9d", "#d9822b", "#3a8f8f", "#8a5a2b", "#a33d6e", "#5c8f3a"];
  async function outbreaks() {
    const rows = await api("/api/expert/outbreaks");
    const diseases = [...new Set(rows.map((r) => r.disease))];
    const color = (d) => PALETTE[diseases.indexOf(d) % PALETTE.length];
    if (!obMap) {
      obMap = L.map("obMap").setView([11.2, 78.2], 7);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 13, attribution: "© OpenStreetMap contributors" }).addTo(obMap);
    }
    setTimeout(() => obMap.invalidateSize(), 50);
    if (obLayer) obLayer.remove();
    obLayer = L.layerGroup(rows.map((r) => L.circleMarker([r.lat, r.lon], {
      radius: 7, color: color(r.disease), fillColor: color(r.disease), fillOpacity: r.source === "simulated" ? 0.35 : 0.85, weight: r.source === "simulated" ? 1 : 2,
      dashArray: r.source === "simulated" ? "3" : null,
    }).bindTooltip(`${esc(r.name_en)}${r.source === "simulated" ? " (simulated)" : ""}<br>${new Date(r.created_at * 1000).toLocaleDateString()}`))).addTo(obMap);
    if (rows.length) obMap.fitBounds(rows.map((r) => [r.lat, r.lon]), { padding: [30, 30], maxZoom: 9 });
    const counts = diseases.map((d) => ({ d, name: rows.find((r) => r.disease === d).name_en, n: rows.filter((r) => r.disease === d).length,
      sim: rows.filter((r) => r.disease === d && r.source === "simulated").length })).sort((a, b) => b.n - a.n);
    $("#obLegend").innerHTML = counts.map((c) => `<span><i class="ob-dot" style="background:${color(c.d)}"></i>${esc(c.name)} (${c.n})</span>`).join("") || '<span class="muted">No reports yet.</span>';
    const sim = rows.filter((r) => r.source === "simulated").length;
    $("#obTable").innerHTML = `<p class="eyebrow">Reports, last 60 days</p><p class="muted small">${rows.length - sim} farmer-confirmed · ${sim} simulated
      ${sim ? "(demo data from scripts/simulate_outbreaks.py — remove with --clear)" : ""}</p>
      <table class="ex"><thead><tr><th>Disease</th><th class="num">Reports</th><th class="num">Simulated</th></tr></thead><tbody>
      ${counts.map((c) => `<tr><td><i class="ob-dot" style="background:${color(c.d)}"></i>${esc(c.name)}</td><td class="num">${c.n}</td><td class="num">${c.sim}</td></tr>`).join("")}</tbody></table>`;
  }

  // ------------------------------------------------------------ teach
  async function teach() {
    const [rows, syms] = await Promise.all([api("/api/expert/unmatched"), SYMPTOMS.length ? SYMPTOMS : api("/api/expert/symptoms")]);
    SYMPTOMS = syms;
    const opts = `<option value="">Map to symptom…</option>` + SYMPTOMS.map((s) => `<option value="${esc(s.id)}">${esc(s.label_en)} — ${esc(s.label_ta)}</option>`).join("");
    $("#p-teach").innerHTML = `
      <h2>Teach the system farmer language</h2>
      <p class="muted">Descriptions the language layer could not map to any symptom. Mapping one creates a new <b>LayTerm</b> node with a
        <code>LAYTERM_MAPS_TO</code> edge in the knowledge graph; it is used immediately. This is how the colloquial vocabulary grows from real usage.</p>
      <div class="card">${rows.length ? rows.map((r) => `
        <div class="teach-row" data-id="${r.id}">
          <div class="q">${esc(r.text)}<small>seen ${r.count}× · last ${new Date(r.last_seen * 1000).toLocaleDateString()}</small></div>
          <select>${opts}</select>
          <select class="lang"><option value="ta">Tamil</option><option value="tl">Tanglish</option><option value="en">English</option></select>
          <button class="btn btn-primary btn-sm" data-resolve>Teach</button>
          <button class="btn btn-ghost btn-sm" data-dismiss>Dismiss</button>
        </div>`).join("") : '<p class="muted">Nothing waiting — every recent description was understood.</p>'}</div>
      <div class="card"><p class="eyebrow">Add a phrase directly</p>
        <div class="add-form"><input type="text" id="newPhrase" placeholder="e.g. இலை மேல வெள்ளை மாவு"><select id="newSym">${opts}</select>
          <select id="newLang"><option value="ta">Tamil</option><option value="tl">Tanglish</option><option value="en">English</option></select>
          <button class="btn btn-primary btn-sm" id="addPhrase">Add lay-term</button></div></div>`;
  }

  // ------------------------------------------------------------ learning
  async function learning() {
    const [edges, sugg] = await Promise.all([api("/api/expert/edges"), api("/api/expert/suggestions")]);
    const learned = edges.filter((e) => e.observations > 0);
    $("#p-learning").innerHTML = `
      <h2>Learning from confirmations</h2>
      <p class="muted">Every HAS_SYMPTOM edge is a Beta(α, β) posterior seeded with 20 pseudo-observations from the literature.
        Farmer-confirmed diagnoses add evidence, so weights move gradually and every change is traceable.</p>
      <div class="card"><p class="eyebrow">Suggested new edges (symptom reported for a confirmed disease that has no such edge)</p>
        ${sugg.length ? `<table class="ex"><thead><tr><th>Disease</th><th>Symptom</th><th class="num">Evidence</th><th></th></tr></thead><tbody>
          ${sugg.map((s) => `<tr><td>${esc(s.disease)}</td><td>${esc(s.symptom)}</td><td class="num">${s.count.toFixed(2)}</td>
          <td><button class="btn btn-primary btn-sm" data-accept="${esc(s.d)}|${esc(s.s)}">Add edge (w=0.3)</button>
              <button class="btn btn-ghost btn-sm" data-reject="${esc(s.d)}|${esc(s.s)}">Reject</button></td></tr>`).join("")}</tbody></table>`
          : '<p class="muted">No suggestions yet.</p>'}</div>
      <div class="card scroll"><p class="eyebrow">Edges updated by feedback (${learned.length} of ${edges.length})</p>
        <table class="ex"><thead><tr><th>Disease</th><th>Symptom</th><th class="num">Seed</th><th class="num">Current</th><th class="num">Drift</th><th class="num">Observations</th></tr></thead><tbody>
        ${(learned.length ? learned : edges.slice(0, 15)).map((e) => `<tr><td>${esc(e.disease)}</td><td>${esc(e.symptom)}</td><td class="num">${e.seed.toFixed(3)}</td>
          <td class="num">${e.current.toFixed(3)}</td><td class="num ${e.drift > 0 ? "pos" : e.drift < 0 ? "neg" : ""}">${e.drift > 0 ? "+" : ""}${e.drift.toFixed(3)}</td>
          <td class="num">${e.observations.toFixed(2)}</td></tr>`).join("")}</tbody></table></div>`;
  }

  // ------------------------------------------------------------ live feedback
  let feedbackFingerprint = "";
  let feedbackLoading = false;
  async function feedback() {
    if (feedbackLoading || document.visibilityState === "hidden") return;
    feedbackLoading = true;
    let data;
    try {
      data = await api("/api/expert/feedback");
      const fingerprint = JSON.stringify(data);
      if (fingerprint === feedbackFingerprint) return;
      feedbackFingerprint = fingerprint;
    const o = data.outcomes || {};
    const changed = data.recent.flatMap((r) => r.weight_updates.map((u) => ({ ...u, outcome: r.outcome, created_at: r.created_at })));
    $("#p-feedback").innerHTML = `
      <div class="feedback-heading">
        <div><h2>Live diagnosis feedback</h2><p class="muted">Real confirmations, corrections and photo-assisted learning updates.</p></div>
        <span class="live-pill"><i></i> Live · 15s refresh</span>
      </div>
      <div class="kpis">
        <div class="kpi"><span>Confirmed</span><b>${o.confirmed || 0}</b></div>
        <div class="kpi"><span>Corrected</span><b>${o.corrected || 0}</b></div>
        <div class="kpi"><span>Rejected / unsure</span><b>${(o.rejected || 0) + (o.unsure || 0)}</b></div>
        <div class="kpi"><span>Feedback with photo</span><b>${data.photo_feedback || 0}</b></div>
      </div>
      <div class="card scroll"><p class="eyebrow">Recent farmer feedback</p>
        <table class="ex feedback-table"><thead><tr><th>Time</th><th>Outcome</th><th>Predicted</th><th>Actual / corrected</th><th>Photo</th><th class="num">Evidence</th><th class="num">Edges changed</th></tr></thead><tbody>
        ${data.recent.map((r) => `<tr>
          <td>${new Date(r.created_at * 1000).toLocaleString()}</td>
          <td><span class="pill ${esc(r.outcome)}">${esc(r.outcome)}</span></td>
          <td>${esc(r.predicted_name || r.predicted_disease || "—")}<small>${r.predicted_probability != null ? Math.round(r.predicted_probability * 100) + "%" : ""}</small></td>
          <td>${esc(r.actual_name || r.actual_disease || "—")}</td>
          <td>${r.photo_used ? `<b>${esc(r.photo_top || "used")}</b><small>${r.photo_probability != null ? Math.round(r.photo_probability * 100) + "%" : ""}</small>` : "No"}</td>
          <td class="num">${r.evidence_count}</td>
          <td class="num">${r.weight_updates.length}</td>
        </tr>`).join("") || '<tr><td colspan="7" class="muted">No feedback received yet.</td></tr>'}
        </tbody></table></div>
      <div class="card scroll"><p class="eyebrow">Live graph-weight changes</p>
        ${changed.length ? `<table class="ex"><thead><tr><th>When</th><th>Outcome</th><th>Disease</th><th>Symptom edge</th><th class="num">Before</th><th class="num">After</th><th class="num">Weight added / reduced</th><th class="num">α</th><th class="num">β</th></tr></thead><tbody>
          ${changed.slice(0, 50).map((u) => `<tr>
            <td>${new Date(u.created_at * 1000).toLocaleTimeString()}</td>
            <td><span class="pill ${esc(u.outcome)}">${esc(u.outcome)}</span></td>
            <td>${esc(u.disease)}</td><td>${esc(u.symptom)}</td>
            <td class="num">${u.before.toFixed(3)}</td><td class="num">${u.after.toFixed(3)}</td>
            <td class="num ${u.delta > 0 ? "pos" : u.delta < 0 ? "neg" : ""}">${u.delta > 0 ? "Added +" : u.delta < 0 ? "Reduced " : "No change "}${u.delta.toFixed(3)}</td>
            <td class="num">${u.alpha.toFixed(3)}</td><td class="num">${u.beta.toFixed(3)}</td>
          </tr>`).join("")}</tbody></table>` : '<p class="muted">No HAS_SYMPTOM edge weights have been updated yet.</p>'}
      </div>`;
    } catch (e) {
      throw e;
    } finally {
      feedbackLoading = false;
    }
  }

  // ------------------------------------------------------------ evaluation
  async function evaluation() {
    const ev = await api("/api/expert/evaluation");
    if (!ev) { $("#p-evaluation").innerHTML = `<h2>Evaluation</h2><p class="callout">No evaluation yet. Run <code>python scripts/evaluate.py</code>.</p>`; return; }
    const m = ev.methods;
    const row = (k, label, fmt = pct) => `<tr><td>${label}</td>${m.map((x) => `<td class="num">${fmt(x[k])}</td>`).join("")}</tr>`;
    $("#p-evaluation").innerHTML = `
      <h2>Evaluation</h2>
      <p class="muted">${esc(ev.description)} Generated ${esc(ev.generated_at)} · ${ev.n_cases} test cases · ${ev.n_runs} simulated dialogues per case.</p>
      <div class="card scroll"><table class="ex"><thead><tr><th>Metric</th>${m.map((x) => `<th class="num">${esc(x.name)}</th>`).join("")}</tr></thead><tbody>
        ${row("text_understood", "Input understood (≥1 symptom matched)")}
        ${row("top1_text_only", "Top-1 accuracy, description only")}
        ${row("top1_final", "Top-1 accuracy after dialogue")}
        ${row("top3_final", "Top-3 accuracy after dialogue")}
        ${row("wrong_confident", "Confidently wrong (≥ 85% on a wrong disease)")}
        ${row("avg_questions", "Avg. follow-up questions", (v) => (v == null ? "—" : v.toFixed(2)))}
        ${Object.keys(m[0].by_lang || {}).map((l) => row_lang(m, l)).join("")}
      </tbody></table></div>
      <div class="card scroll"><p class="eyebrow">Per disease — top-1 after dialogue</p>
        <table class="ex"><thead><tr><th>Disease</th><th class="num">Cases</th>${m.map((x) => `<th class="num">${esc(x.name)}</th>`).join("")}</tr></thead><tbody>
        ${ev.per_disease.map((d) => `<tr><td>${esc(d.name)}</td><td class="num">${d.n}</td>${m.map((x) => `<td class="num">${pct(d[x.id])}</td>`).join("")}</tr>`).join("")}
        </tbody></table></div>
      <p class="callout">${esc(ev.caveat)}</p>`;
    function row_lang(ms, l) {
      const name = { ta: "Tamil", en: "English", tl: "Tanglish" }[l] || l;
      return `<tr><td>Top-1 after dialogue — ${name} inputs</td>${ms.map((x) => `<td class="num">${pct(x.by_lang[l])}</td>`).join("")}</tr>`;
    }
  }

  // ------------------------------------------------------------ vision
  async function visionPanel() {
    const v = await api("/api/expert/vision");
    if (!v) { $("#p-vision").innerHTML = `<h2>Photo model</h2><p class="callout">No model loaded. Run <code>python scripts/train_vision.py</code>.</p>`; return; }
    const L = v.labels, cm = v.confusion_matrix;
    const short = (s) => s.replace("_virus", "").replace("_leaf_spot", "").replace("bacterial_", "bact. ").replace(/_/g, " ");
    const cell = (n, i, j) => {
      const tot = cm[i].reduce((a, b) => a + b, 0) || 1, f = n / tot;
      const bg = i === j ? `rgba(47,125,58,${0.15 + f * 0.85})` : n ? `rgba(200,67,43,${0.15 + f * 2})` : "transparent";
      return `<td style="background:${bg};color:${f > 0.5 ? "#fff" : "inherit"}">${n || ""}</td>`;
    };
    $("#p-vision").innerHTML = `
      <h2>Leaf-photo classifier</h2>
      <div class="kpis">
        <div class="kpi"><span>Validation accuracy</span><b>${pct(v.val_accuracy)}</b><small>${v.val_images} held-out images</small></div>
        <div class="kpi"><span>Classes</span><b>${L.length}</b><small>9 diseases + healthy</small></div>
        <div class="kpi"><span>Backbone</span><b style="font-size:16px">${esc(v.backbone)}</b><small>trained ${esc(v.trained_at)}</small></div>
        <div class="kpi"><span>Calibration temperature</span><b>${v.temperature}</b></div>
      </div>
      <div class="grid2">
        <div class="card scroll"><p class="eyebrow">Per class</p><table class="ex"><thead><tr><th>Class</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">F1</th></tr></thead><tbody>
          ${L.map((l) => `<tr><td>${esc(l)}</td><td class="num">${pct(v.per_class[l].precision)}</td><td class="num">${pct(v.per_class[l].recall)}</td><td class="num">${pct(v.per_class[l].f1)}</td></tr>`).join("")}</tbody></table></div>
        <div class="card scroll"><p class="eyebrow">Confusion matrix (rows = truth)</p>
          <table class="cm"><tr><th></th>${L.map((l) => `<th title="${esc(l)}">${esc(short(l)).slice(0, 6)}</th>`).join("")}</tr>
          ${cm.map((r, i) => `<tr><th class="rowh">${esc(short(L[i]))}</th>${r.map((n, j) => cell(n, i, j)).join("")}</tr>`).join("")}</table></div>
      </div>
      <p class="callout">${esc(v.note)}</p>`;
  }

  // ------------------------------------------------------------ add disease
  let TREATMENTS = [];
  async function addDisease() {
    const [syms, trts] = await Promise.all([
      SYMPTOMS.length ? SYMPTOMS : api("/api/expert/symptoms"),
      TREATMENTS.length ? TREATMENTS : api("/api/expert/treatments"),
    ]);
    SYMPTOMS = syms; TREATMENTS = trts;

    const symOpts = syms.map(s => `<option value="${esc(s.id)}">${esc(s.label_en)} — ${esc(s.label_ta)}</option>`).join("");
    const trtOpts = trts.map(t => `<option value="${esc(t.id)}">[${esc(t.type)}] ${esc(t.name_en)}</option>`).join("");
    const seasons = ["humid_monsoon", "cool_moist", "hot_dry"];
    const seasonLabels = { humid_monsoon: "Humid / Monsoon", cool_moist: "Cool & Misty", hot_dry: "Hot & Dry" };

    $("#p-add-disease").innerHTML = `
      <h2>Add a new disease to the knowledge graph</h2>
      <p class="muted">This creates a live disease entry with symptom links, treatment links, and seasonal preferences.
        The new disease is immediately available for diagnosis — no restart required.</p>

      <div class="card add-disease-form">
        <p class="eyebrow">① Identity</p>
        <div class="add-disease-grid">
          <label>Disease ID (slug)<small>lowercase, underscores, e.g. powdery_mildew</small>
            <input type="text" id="did" placeholder="powdery_mildew"></label>
          <label>Name (English)<input type="text" id="dname_en" placeholder="Powdery Mildew"></label>
          <label>Name (Tamil)<input type="text" id="dname_ta" placeholder="வெண்தூள் நோய்"></label>
          <label>Type
            <select id="dtype">
              <option value="fungal">Fungal</option><option value="bacterial">Bacterial</option>
              <option value="viral">Viral</option><option value="pest">Pest</option>
              <option value="physiological">Physiological</option><option value="other">Other</option>
            </select></label>
          <label>Severity (1=mild, 5=critical)
            <input type="range" id="dseverity" min="1" max="5" value="3" oninput="this.nextElementSibling.textContent=this.value">
            <output>3</output></label>
          <label class="checkbox-row"><input type="checkbox" id="dcontagious"> Contagious (spreads plant-to-plant)</label>
        </div>

        <p class="eyebrow" style="margin-top:18px">② Description</p>
        <div class="add-disease-grid">
          <label>Summary (English)<textarea id="dsummary_en" rows="3" placeholder="Describe the disease in English…"></textarea></label>
          <label>Summary (Tamil)<textarea id="dsummary_ta" rows="3" placeholder="தமிழில் விவரிக்கவும்…"></textarea></label>
        </div>

        <p class="eyebrow" style="margin-top:18px">③ Symptom links <small class="muted">(at least one required)</small></p>
        <p class="muted small">These become HAS_SYMPTOM edges. Weight ≈ P(symptom visible | disease). 0.8 = strongly associated.</p>
        <div id="symLinks"></div>
        <div class="add-form" style="margin-top:8px">
          <select id="addSymSel"><option value="">Add a symptom…</option>${symOpts}</select>
          <input type="number" id="addSymW" min="0.05" max="0.95" step="0.05" value="0.6" style="max-width:90px" title="Weight">
          <button class="btn btn-ghost btn-sm" id="addSymBtn">+ Add</button>
        </div>

        <p class="eyebrow" style="margin-top:18px">④ Treatment links <small class="muted">(at least one required)</small></p>
        <p class="muted small">These become TREATED_BY edges. Efficacy ≈ how effective this treatment is (0-1).</p>
        <div id="trtLinks"></div>
        <div class="add-form" style="margin-top:8px">
          <select id="addTrtSel"><option value="">Add a treatment…</option>${trtOpts}</select>
          <input type="number" id="addTrtEff" min="0.01" max="1.0" step="0.05" value="0.6" style="max-width:90px" title="Efficacy">
          <button class="btn btn-ghost btn-sm" id="addTrtBtn">+ Add</button>
        </div>

        <p class="eyebrow" style="margin-top:18px">⑤ Seasonal preference <small class="muted">(optional)</small></p>
        <div class="add-disease-grid">
          ${seasons.map(s => `<label>${seasonLabels[s]} boost
            <input type="range" class="season-boost" data-season="${s}" min="0" max="2" step="0.1" value="0"
              oninput="this.nextElementSibling.textContent=parseFloat(this.value).toFixed(1)">
            <output>0.0</output></label>`).join("")}
        </div>

        <div style="margin-top:22px;display:flex;gap:12px;align-items:center">
          <button class="btn btn-primary" id="submitDiseaseBtn">Add disease to graph</button>
          <span id="diseaseFormMsg" style="font-size:14px"></span>
        </div>
      </div>`;

    // track added symptom/treatment links
    const symLinks = [], trtLinks = [];

    function renderSymLinks() {
      $("#symLinks").innerHTML = symLinks.map((l, i) => {
        const s = syms.find(x => x.id === l.sid);
        return `<div class="teach-row" style="grid-template-columns:2fr 120px auto">
          <span>${esc(s ? s.label_en : l.sid)}</span>
          <span class="muted small">weight ${l.w.toFixed(2)}</span>
          <button class="btn btn-ghost btn-sm" data-rmsym="${i}">✕</button></div>`;
      }).join("") || '<p class="muted small">No symptoms added yet.</p>';
    }
    function renderTrtLinks() {
      $("#trtLinks").innerHTML = trtLinks.map((l, i) => {
        const t = trts.find(x => x.id === l.tid);
        return `<div class="teach-row" style="grid-template-columns:2fr 120px auto">
          <span>${esc(t ? t.name_en : l.tid)}</span>
          <span class="muted small">efficacy ${l.eff.toFixed(2)}</span>
          <button class="btn btn-ghost btn-sm" data-rmtrt="${i}">✕</button></div>`;
      }).join("") || '<p class="muted small">No treatments added yet.</p>';
    }
    renderSymLinks(); renderTrtLinks();

    // dynamic button wiring inside the panel (delegated to section)
    const panel = $("#p-add-disease");
    panel.addEventListener("click", async e => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.id === "addSymBtn") {
        const sid = $("#addSymSel").value;
        if (!sid) return;
        const w = parseFloat($("#addSymW").value) || 0.6;
        if (!symLinks.find(l => l.sid === sid)) symLinks.push({ sid, w });
        renderSymLinks(); return;
      }
      if (b.id === "addTrtBtn") {
        const tid = $("#addTrtSel").value;
        if (!tid) return;
        const eff = parseFloat($("#addTrtEff").value) || 0.6;
        if (!trtLinks.find(l => l.tid === tid)) trtLinks.push({ tid, eff });
        renderTrtLinks(); return;
      }
      if (b.dataset.rmsym !== undefined) { symLinks.splice(+b.dataset.rmsym, 1); renderSymLinks(); return; }
      if (b.dataset.rmtrt !== undefined) { trtLinks.splice(+b.dataset.rmtrt, 1); renderTrtLinks(); return; }
      if (b.id === "submitDiseaseBtn") {
        const msg = $("#diseaseFormMsg");
        const favored_by = {};
        $$(".season-boost").forEach(el => { if (+el.value > 0) favored_by[el.dataset.season] = +el.value; });
        const payload = {
          id: $("#did").value.trim(),
          name_en: $("#dname_en").value.trim(), name_ta: $("#dname_ta").value.trim(),
          type: $("#dtype").value, severity: +$("#dseverity").value,
          contagious: $("#dcontagious").checked,
          summary_en: $("#dsummary_en").value.trim(), summary_ta: $("#dsummary_ta").value.trim(),
          symptoms: symLinks.map(l => ({ symptom_id: l.sid, weight: l.w })),
          treatments: trtLinks.map(l => ({ treatment_id: l.tid, efficacy: l.eff })),
          favored_by,
        };
        msg.textContent = "Saving…"; msg.style.color = "var(--muted)";
        try {
          const r = await api("/api/expert/disease", payload);
          msg.textContent = `✓ Disease '${r.disease_id}' added to the graph!`;
          msg.style.color = "var(--ok)";
        } catch (err) {
          msg.textContent = `✗ ${err.message}`;
          msg.style.color = "var(--no)";
        }
      }
    });
  }

  // ------------------------------------------------------------ wiring
  const PANELS = { overview, graph, outbreaks, teach, add_disease: addDisease, learning, feedback, evaluation, vision: visionPanel };
  let liveTimer = null;
  async function open(tab) {
    if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
    $$("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
    $$("[data-panel]").forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== tab));
    if (location.hash.slice(1) !== tab) history.replaceState(null, "", "#" + tab);
    try { await PANELS[tab](); } catch (e) { if (e.message !== "locked") console.error(e); }
    if (tab === "feedback") liveTimer = setInterval(feedback, 15000);
  }
  document.addEventListener("click", async (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.tab) return open(b.dataset.tab);
    if (b.id === "tokenSave") { token = $("#tokenInput").value; sessionStorage.setItem("expertToken", token); $("#tokenBox").classList.add("hidden"); return open(location.hash.slice(1) || "overview"); }
    const row = b.closest(".teach-row");
    if (b.dataset.resolve !== undefined) {
      const sid = $("select", row).value;
      if (!sid) return alert("Choose the symptom this phrase describes.");
      await api(`/api/expert/unmatched/${row.dataset.id}/resolve`, { symptom_id: sid, lang: $("select.lang", row).value });
      return teach();
    }
    if (b.dataset.dismiss !== undefined) { await api(`/api/expert/unmatched/${row.dataset.id}/dismiss`, {}); return teach(); }
    if (b.id === "addPhrase") {
      const text = $("#newPhrase").value.trim(), sid = $("#newSym").value;
      if (!text || !sid) return alert("Enter a phrase and choose a symptom.");
      await api("/api/expert/layterm", { text, symptom_id: sid, lang: $("#newLang").value });
      $("#newPhrase").value = ""; alert("Lay-term added to the knowledge graph."); return;
    }
    if (b.dataset.accept) { const [d, s] = b.dataset.accept.split("|"); await api("/api/expert/suggestions/accept", { d, s, weight: 0.3 }); return learning(); }
    if (b.dataset.reject) { const [d, s] = b.dataset.reject.split("|"); await api("/api/expert/suggestions/reject", { d, s }); return learning(); }
  });
  $("#graphFull").addEventListener("click", toggleFull);
  document.addEventListener("fullscreenchange", syncFullUi);
  document.addEventListener("webkitfullscreenchange", syncFullUi);
  document.addEventListener("keydown", (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);
    if (e.key === "Escape" && wrap().classList.contains("pseudo-full")) { wrap().classList.remove("pseudo-full"); syncFullUi(); }
    else if ((e.key === "f" || e.key === "F") && !typing && !e.ctrlKey && !e.metaKey && !e.altKey
             && !$("[data-panel=graph]").classList.contains("hidden")) { e.preventDefault(); toggleFull(); }
  });
  $("#showLayterms").addEventListener("change", graph);
  $("#showTreatments").addEventListener("change", drawGraph);
  $("#graphSearch").addEventListener("change", (e) => {
    if (!network || !graphData) return;
    const q = e.target.value.toLowerCase();
    const hit = graphData.nodes.find((n) => n.label.toLowerCase().includes(q) || (n.label_ta || "").includes(q));
    if (hit) { network.selectNodes([hit.id]); network.focus(hit.id, { scale: 1.3, animation: false }); }
  });
  fetch("/api/meta").then((r) => r.json()).then((m) => { $("#backendPill").textContent = `Graph: ${m.backend.backend} · v${m.kg_version}`; }).catch(() => {});
  window.addEventListener("hashchange", () => { const t = location.hash.slice(1); if (PANELS[t]) open(t); });
  open(PANELS[location.hash.slice(1)] ? location.hash.slice(1) : "overview");
})();
