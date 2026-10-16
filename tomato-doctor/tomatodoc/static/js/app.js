/* Tomato Doctor – farmer app (vanilla JS, no build step). */
(() => {
  "use strict";

  // ---------------------------------------------------------------- helpers
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
  };
  const pct = (p) => Math.round(p * 100);
  const daysText = (n) => (n === 1 ? t("days_1") : t("days_n", { n }));
  const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10));

  let L = store.get("lang", "ta");
  const t = (k, vars) => {
    let s = (I18N[L] && I18N[L][k]) ?? I18N.en[k] ?? k;
    if (vars) for (const [a, b] of Object.entries(vars)) s = s.replaceAll(`{${a}}`, b);
    return s;
  };
  const loc = (o, f) => (o ? o[`${f}_${L}`] ?? o[`${f}_${L === "ta" ? "en" : "ta"}`] ?? "" : "");
  const other = (o, f) => (o ? o[`${f}_${L === "ta" ? "en" : "ta"}`] ?? "" : "");
  const icon = (id) => `<svg aria-hidden="true"><use href="#i-${id}"/></svg>`;

  // ---------------------------------------------------------------- state
  let META = null;
  const S = {
    sessionId: uuid(), text: "", textMatches: [], answers: [], skipped: [], picked: new Set(),
    photo: null, photoUrl: null, season: store.get("season", null), weather: null,
    last: null, feedbackSent: false,
    location: store.get("location", null), ctx: null, locState: null, ctxLoading: false,
    soil: store.get("soil", null), crop: store.get("crop", "variety"), field: store.get("field", null), view: null, prevView: null,
    severity: null, extent: null, sevByUser: false, extByUser: false, sprays: [], ai: null,
  };
  const resetConsult = (keepInputs = false) => {
    S.sessionId = uuid(); S.answers = []; S.skipped = []; S.last = null; S.feedbackSent = false; S.textMatches = [];
    if (!keepInputs) {
      S.text = ""; S.picked = new Set(); S.photo = null; S.photoUrl = null; $("#farmerInput").value = "";
      S.severity = null; S.extent = null; S.sevByUser = false; S.extByUser = false; S.sprays = []; S.ai = null;
      renderSegs(); renderSprays(); renderAiBox();
    }
  };

  // ---------------------------------------------------------------- api
  const loading = (on) => $("#loading").classList.toggle("hidden", !on);
  async function api(path, body, opts = {}) {
    loading(true);
    try {
      const init = body instanceof FormData ? { method: "POST", body }
        : body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
      const res = await fetch(path, init);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { const e = new Error(data.error || res.statusText); e.status = res.status; throw e; }
      return data;
    } catch (e) {
      if (!opts.quiet) toast(navigator.onLine ? t("error") : t("offline"));
      throw e;
    } finally { loading(false); }
  }

  // ---------------------------------------------------------------- ui basics
  let toastTimer;
  function toast(msg, ms = 3200) {
    const el = $("#toast"); el.textContent = msg; el.classList.remove("hidden");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.add("hidden"), ms);
  }

  const THEMES = ["auto", "light", "dark"];
  function applyTheme() {
    const th = store.get("theme", "auto");
    if (th === "auto") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = th;
    $("#themeIcon").setAttribute("href", th === "light" ? "#i-sun" : th === "dark" ? "#i-moon" : "#i-contrast");
    $("#themeBtn").title = t("theme_" + th);
    $("#themeBtn").setAttribute("aria-label", t("theme_" + th));
  }
  function applyI18n() {
    document.documentElement.lang = L;
    document.body.classList.toggle("lang-ta", L === "ta");
    document.body.classList.toggle("lang-en", L === "en");
    $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $$("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    $$("[data-i18n-title]").forEach((el) => { el.title = t(el.dataset.i18nTitle); el.setAttribute("aria-label", t(el.dataset.i18nTitle)); });
    $$("#langToggle [data-lang]").forEach((el) => el.classList.toggle("on", el.dataset.lang === L));
    document.title = `${t("app_name")} · ${L === "ta" ? "Tomato Doctor" : "தக்காளி டாக்டர்"}`;
  }

  const VIEWS = ["home", "consult", "result", "library", "disease", "history", "field"];
  const NAV_OF = { home: "home", consult: "home", result: "home", field: "field", library: "library", disease: "library", history: "history" };
  const TITLE_OF = { home: "nav_diagnose", consult: "page_consult", result: "page_result", field: "nav_field",
    library: "nav_library", disease: "page_disease", history: "nav_history" };
  function updateShell() {
    const v = S.view || "home";
    $$("[data-nav-item]").forEach((b) => b.classList.toggle("active", b.dataset.navItem === NAV_OF[v]));
    $("#crumbTitle").textContent = t(TITLE_OF[v]);
    document.body.dataset.view = v;
  }
  function show(view) {
    if (view !== S.view) { S.prevView = S.view; S.view = view; }
    VIEWS.forEach((v) => $(`#view-${v}`).classList.toggle("hidden", v !== view));
    updateShell();
    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  }
  function navigate(hash) { if (location.hash === `#${hash}`) route(); else location.hash = hash; }
  function route() {
    const [view, arg] = location.hash.replace(/^#/, "").split("/");
    switch (view) {
      case "library": renderLibrary(); return show("library");
      case "disease": return openDisease(arg);
      case "history": renderHistory(); return show("history");
      case "field": renderMyField(arg); return show("field");
      case "soil": return navigate("field/soil");
      case "consult": if (S.last && S.last.status === "question") { renderConsult(); return show("consult"); } break;
      case "result": if (S.last && S.last.status === "result") { renderResult(); return show("result"); } break;
    }
    renderHome(); show("home");
  }

  // ---------------------------------------------------------------- speech
  const voices = () => (window.speechSynthesis ? speechSynthesis.getVoices() : []);
  const voiceFor = (lang) => voices().find((v) => v.lang.toLowerCase().startsWith(lang));
  function canSpeak() { return !!window.speechSynthesis && !!voiceFor(L === "ta" ? "ta" : "en"); }
  function speak(text) {
    if (!window.speechSynthesis) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const v = voiceFor(L === "ta" ? "ta" : "en");
    if (v) u.voice = v;
    u.lang = L === "ta" ? "ta-IN" : "en-IN";
    u.rate = 0.95;
    speechSynthesis.speak(u);
  }
  function setupMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const btn = $("#micBtn");
    if (META && META.voice_ai.available && window.MediaRecorder && navigator.mediaDevices) {
      btn.addEventListener("click", geminiMic);
      return;
    }
    if (!SR) { btn.classList.add("hidden"); return; }
    let rec = null;
    btn.addEventListener("click", () => {
      if (rec) { rec.stop(); return; }
      rec = new SR();
      rec.lang = L === "ta" ? "ta-IN" : "en-IN";
      rec.interimResults = true;
      rec.continuous = false;
      const input = $("#farmerInput");
      const base = input.value ? input.value.trim() + " " : "";
      rec.onresult = (e) => {
        const txt = [...e.results].map((r) => r[0].transcript).join(" ");
        input.value = base + txt;
      };
      rec.onend = () => { rec = null; btn.classList.remove("active"); $("#listening").classList.add("hidden"); };
      rec.onerror = () => { rec = null; };
      btn.classList.add("active"); $("#listening").classList.remove("hidden");
      rec.start();
    });
  }

  // ---------------------------------------------------------------- home
  function seasonText() {
    const s = META && META.seasons.find((x) => x.id === (S.season || (S.last && S.last.season && S.last.season.id) || META.season_suggestion.id));
    const sid = S.season || (S.ctx && S.ctx.season) || (META && META.season_suggestion.id);
    const s2 = META && META.seasons.find((x) => x.id === sid);
    const src = S.season ? t("season_src_farmer") : S.ctx && S.ctx.season ? t("season_src_weather") : t("season_src_calendar");
    return s2 ? `${loc(s2, "name")} · ${src}` : (s ? loc(s, "name") : t("season_auto"));
  }
  function renderHome() {
    $("#exampleChips").innerHTML = EXAMPLES[L].map((e) => `<button class="chip" data-example="${esc(e)}">${esc(e)}</button>`).join("");
    $("#seasonLabel").textContent = seasonText();
    $("#locLabel").textContent = locLabel();
    renderFieldChip();
    if (S.view === "field") $("#fieldLocLabel").textContent = S.location ? locLabel() : t("field_loc_none");
    renderAttachments(); renderField(); renderSegs(); renderSprays(); renderAiBox(); renderKgCard();
  }
  function renderKgCard() {
    if (!META) return;
    const k = META.kg, acc = META.vision && META.vision.val_accuracy;
    const stat = (v, label) => `<div class="stat"><b>${esc(v)}</b><span>${esc(t(label))}</span></div>`;
    $("#kgCard").innerHTML = `<p class="eyebrow">${esc(t("kg_title"))}</p>
      <p class="muted small">${esc(t("kg_sub"))}</p>
      <div class="stats">${stat(k.diseases, "stat_diseases")}${stat(k.layterms, "stat_phrases")}${stat(k.treatments, "stat_treatments")}
        ${acc ? stat(`${(acc * 100).toFixed(1)}%`, "stat_photo") : ""}</div>
      <p class="kg-langs">${icon("leaf")}<span>${esc(t("kg_langs"))}</span></p>
      ${!S.location && !S.locState ? `<button class="kg-loc" data-act="loc-pick">${icon("pin")}<span>${esc(t("kg_loc_cta"))}</span>${icon("arrow")}</button>` : ""}`;
  }
  function renderAttachments() {
    const parts = [];
    if (S.photoUrl) {
      let label = "…";
      if (S.photo) {
        const top = S.photo.ranked[0];
        label = top.id === "healthy" ? t("photo_healthy") : `${t("photo_says")}: ${loc(top, "name")} ${pct(top.p)}%`;
      }
      parts.push(`<div class="attach photo-attach"><img src="${S.photoUrl}" alt=""><span>${esc(label)}</span>
        <button class="icon-btn" data-remove-photo aria-label="${esc(t("photo_remove"))}">${icon("x")}</button></div>`);
      if (S.photo && S.photo.quality.issues.length) parts.push(`<p class="warn">${icon("alert")} ${S.photo.quality.issues.map((i) => esc(t("photo_issue_" + i))).join(" · ")}</p>`);
    }
    if (S.picked.size) {
      parts.push(`<div class="attach"><span>${icon("grid")} ${[...S.picked].map((id) => esc(symptomLabel(id))).join(" · ")}</span>
        <button class="icon-btn" data-clear-picked aria-label="clear">${icon("x")}</button></div>`);
    }
    $("#attachments").innerHTML = parts.join("");
  }
  function symptomLabel(id) {
    for (const g of META.symptom_groups) { const s = g.items.find((x) => x.id === id); if (s) return loc(s, "label"); }
    return id;
  }

  async function startDiagnosis() {
    const text = $("#farmerInput").value.trim();
    if (!text && !S.photoUrl && !S.picked.size) { toast(t("empty_input")); $("#farmerInput").focus(); return; }
    resetConsult(true);
    S.text = text;
    if (text) {
      let a;
      try { a = await api("/api/analyze", { text }); } catch { return; }
      S.textMatches = a.matches;
      if (a.ai) S.ai = a.ai;
      applyModifiers(a.modifiers, a.ai);
    }
    await runDiagnose();
  }

  async function runDiagnose(extra = {}) {
    const body = {
      session_id: S.sessionId, text: S.text, lang: L, text_matches: S.textMatches, answers: S.answers, skipped: S.skipped,
      picked: [...S.picked].map((id) => ({ symptom_id: id, present: true })),
      photo: S.photo ? { probs: S.photo.probs, temperature: S.photo.temperature } : null,
      season: S.season, location: S.location ? { lat: S.location.lat, lon: S.location.lon } : null,
      severity: S.severity, extent: S.extent, sprays: S.sprays,
      ai_symptoms: S.ai ? S.ai.symptoms : [], soil: S.soil, crop_type: cropType(), field: fieldPayload(), ...extra,
    };
    let res;
    try { res = await api("/api/diagnose", body); } catch { return; }
    S.last = res;
    if (res.status === "need_input") {
      navigate("home");
      toast(t("need_input"), 6000);
      openPicker();
      return;
    }
    if (res.status === "question") navigate("consult");
    else { saveHistory(); navigate("result"); }
  }

  // ---------------------------------------------------------------- location & field conditions
  // The app asks for the farmer's location as soon as it opens (browser permission prompt).
  // A district chosen by hand is respected; a GPS location is refreshed on every visit.
  const isGps = (l) => !!l && (l.src === "gps" || (!l.src && !l.label && l.idx == null));
  function kmBetween(a, b, c, d) {
    const r = Math.PI / 180, h = Math.sin((c - a) * r / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin((d - b) * r / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(h));
  }
  function nearestDistrict(lat, lon) {
    let best = null, bd = Infinity;
    TN_DISTRICTS.forEach(([, , la, lo], i) => { const k = kmBetween(lat, lon, la, lo); if (k < bd) { bd = k; best = i; } });
    return bd <= 75 ? best : null;
  }
  const districtName = (i) => (TN_DISTRICTS[i] ? TN_DISTRICTS[i][L === "ta" ? 1 : 0] : "");
  function locLabel() {
    const l = S.location;
    if (!l) return t("loc_use");
    if (isGps(l)) return l.near != null ? t("loc_near", { d: districtName(l.near) }) : `${l.lat.toFixed(2)}, ${l.lon.toFixed(2)}`;
    return l.idx != null ? districtName(l.idx) : (l.label || `${l.lat.toFixed(2)}, ${l.lon.toFixed(2)}`);
  }
  async function setLocation(l) {
    S.location = l; S.locState = null;
    store.set("location", S.location);
    closeSheets();
    renderHome();
    await loadContext();
  }
  async function loadContext() {
    if (!S.location) { S.ctx = null; renderField(); return; }
    S.ctxLoading = true; renderField();
    try { S.ctx = await api("/api/context", { lat: S.location.lat, lon: S.location.lon, field: fieldPayload() }, { quiet: true }); } catch { S.ctx = null; }
    S.ctxLoading = false;
    renderHome();
  }
  function openLocSheet() {
    $("#districtList").innerHTML = TN_DISTRICTS.map(([en, ta, la, lo], i) =>
      `<button class="option" data-district="${la},${lo}" data-idx="${i}"><span>${esc(L === "ta" ? ta : en)}</span><small>${esc(L === "ta" ? en : ta)}</small></button>`).join("");
    $("#locClear").classList.toggle("hidden", !S.location);
    openSheet("#locSheet");
  }
  function locate(showAsking, announce) {
    if (!window.isSecureContext || !navigator.geolocation) {
      if (!S.location) { S.locState = "insecure"; renderField(); }
      if (announce) toast(t("loc_insecure"), 5000);
      return;
    }
    if (showAsking) { S.locState = "asking"; renderField(); }
    navigator.geolocation.getCurrentPosition((p) => {
      const lat = +p.coords.latitude.toFixed(3), lon = +p.coords.longitude.toFixed(3);
      const first = !S.location;
      setLocation({ lat, lon, src: "gps", near: nearestDistrict(lat, lon) });
      if (first || announce) toast(t("loc_found", { d: locLabel() }));
    }, (err) => {
      if (S.location) return;                         // keep the last known location
      S.locState = err && err.code === 1 ? "denied" : "error";
      renderField();
      if (announce) toast(t("loc_fail"), 4500);
    }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 600e3 });
  }
  async function autoLocate() {
    if (S.location && !isGps(S.location)) return;     // farmer picked a district: respect it
    let perm = "prompt";
    try { perm = (await navigator.permissions.query({ name: "geolocation" })).state; } catch { /* older Safari */ }
    if (perm === "denied") { if (!S.location) { S.locState = "denied"; renderField(); } return; }
    locate(!S.location, false);
  }
  function gps() { closeSheets(); locate(true, true); }
  const riskName = (m) => t(m === "hutton" ? "risk_model_hutton" : m === "tomcast" ? "risk_model_tomcast" : "risk_model_rule");
  function wxLine(w) {
    if (!w) return `<p class="muted">${esc(t("wx_unavailable"))}</p>`;
    return `<p class="wx">${icon("cloud")} ${esc(t("wx_now", { t: Math.round(w.temp), h: Math.round(w.rh), w: Math.round(w.wind) }))}</p>
      <p class="wx sub">${esc(t("wx_rain24", { r: w.rain_next_24h_mm }))}</p>`;
  }
  function outbreakLines(ob) {
    if (!ob || !ob.diseases.length) return "";
    return ob.diseases.slice(0, 3).map((o) => `<p class="outbreak">${icon("alert")} ${esc(t("outbreak_alert", { n: o.n, d: loc(o, "name"), km: ob.radius_km, days: ob.days, cases: o.n === 1 ? "case" : "cases" }))}
      ${o.simulated ? `<small>${esc(t("outbreak_sim"))}</small>` : ""}</p>`).join("");
  }
  function renderField() {
    renderKgCard();
    const box = $("#fieldCard");
    if (!S.location) {
      const st = S.locState;
      if (!st) { box.classList.add("hidden"); return; }
      box.innerHTML = st === "asking"
        ? `<p class="loc-ask"><span class="pulse"></span><span>${esc(t("loc_asking"))}</span></p><p class="muted small">${esc(t("loc_why"))}</p>`
        : `<p class="loc-ask warn-ask">${icon("pin")}<span>${esc(t(st === "denied" ? "loc_denied" : st === "insecure" ? "loc_insecure" : "loc_fail"))}</span></p>
           <p class="muted small">${esc(t("loc_why"))}</p>
           <div class="loc-actions"><button class="btn btn-primary btn-sm" data-act="loc-pick">${icon("pin")}<span>${esc(t("loc_pick"))}</span></button>
           ${st === "error" ? `<button class="btn btn-ghost btn-sm" data-act="loc-retry">${esc(t("loc_allow"))}</button>` : ""}</div>`;
      box.classList.remove("hidden");
      return;
    }
    if (!S.ctx) {
      if (!S.ctxLoading) { box.classList.add("hidden"); return; }
      box.innerHTML = `<p class="loc-ask"><span class="pulse"></span><span>${esc(t("wx_loading"))}</span></p>`;
      box.classList.remove("hidden");
      return;
    }
    const c = S.ctx;
    const risks = (c.risks || []).filter((r) => r.level !== "low").slice(0, 5);
    box.innerHTML = `<div class="card-head"><p class="eyebrow">${esc(t("field_title"))} · ${esc(locLabel())}</p></div>
      ${wxLine(c.weather)}${outbreakLines(c.outbreaks)}${alertsHtml(c.alerts)}
      <p class="eyebrow" style="margin-top:14px">${esc(t("risk_title"))}</p>
      ${risks.length ? `<div class="risk-list">${risks.map((r) => `<a class="risk-row" href="#disease/${esc(r.disease_id)}">
          <span class="lvl ${esc(r.level)}">${esc(t("risk_" + r.level))}</span>
          <span class="risk-name">${esc(loc(r, "name"))}<small>${esc(loc(r, "explain") || riskName(r.model))}</small></span>
          <span class="risk-bar"><i style="width:${pct(r.score)}%"></i></span></a>`).join("")}</div>`
        : `<p class="muted">${esc(t("risk_none"))}</p>`}`;
    box.classList.remove("hidden");
  }

  // ---------------------------------------------------------------- severity / extent / sprays
  function applyModifiers(m, ai) {
    if (m && m.severity && !S.sevByUser) S.severity = m.severity;
    if (m && m.affected_percent != null && !S.extByUser) S.extent = m.affected_percent;
    if (ai && ai.sprays_done) for (const sp of ai.sprays_done) if (!S.sprays.some((x) => x.product === sp.product)) S.sprays.push(sp);
    renderSegs(); renderSprays();
  }
  function renderSegs() {
    $$("#sevSeg [data-sev]").forEach((b) => b.classList.toggle("on", b.dataset.sev === S.severity));
    const ext = S.extent == null ? null : S.extent < 15 ? "5" : S.extent < 60 ? "30" : "80";
    $$("#extSeg [data-ext]").forEach((b) => b.classList.toggle("on", b.dataset.ext === ext));
    if (S.severity || S.extent != null || S.sprays.length) $("#moreDetails").open = true;
  }
  function renderSprays() {
    $("#sprayChips").innerHTML = S.sprays.map((sp, i) => `<button class="chip on" data-spray-del="${i}">${esc(sp.product)}${sp.days_ago != null ? " · " + esc(t("days_n", { n: sp.days_ago })) : ""} ✕</button>`).join("");
  }

  // ---------------------------------------------------------------- voice (Gemini) + AI findings
  function renderAiBox() {
    const box = $("#aiBox"), ai = S.ai;
    if (!ai || (!ai.transcript && !(ai.symptoms || []).length)) { box.classList.add("hidden"); return; }
    box.innerHTML = `${ai.transcript ? `<p class="eyebrow">${icon("mic")} ${esc(t("ai_heard"))}</p><p class="transcript">“${esc(ai.transcript)}”</p>` : ""}
      ${(ai.symptoms || []).length ? `<p class="eyebrow">${esc(t("ai_found"))}</p><div class="chips">${ai.symptoms.map((x) =>
        `<span class="chip ai-chip ${x.present ? "" : "absent"}">${esc(loc(x, "label"))}${x.present ? "" : " — " + esc(t("evidence_absent"))}</span>`).join("")}</div>` : ""}
      <p class="muted small">${esc(t("ai_note"))}</p>`;
    box.classList.remove("hidden");
  }
  async function toWav(blob) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const audio = await new Ctx().decodeAudioData(await blob.arrayBuffer());
    const rate = 16000;
    const off = new OfflineAudioContext(1, Math.ceil(audio.duration * rate), rate);
    const src = off.createBufferSource(); src.buffer = audio; src.connect(off.destination); src.start();
    const pcm = (await off.startRendering()).getChannelData(0);
    const dv = new DataView(new ArrayBuffer(44 + pcm.length * 2));
    const str = (o, x) => [...x].forEach((ch, i) => dv.setUint8(o + i, ch.charCodeAt(0)));
    str(0, "RIFF"); dv.setUint32(4, 36 + pcm.length * 2, true); str(8, "WAVE"); str(12, "fmt ");
    dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true); dv.setUint32(24, rate, true);
    dv.setUint32(28, rate * 2, true); dv.setUint16(32, 2, true); dv.setUint16(34, 16, true); str(36, "data"); dv.setUint32(40, pcm.length * 2, true);
    for (let i = 0; i < pcm.length; i++) dv.setInt16(44 + i * 2, Math.max(-1, Math.min(1, pcm[i])) * 0x7fff, true);
    return new Blob([dv], { type: "audio/wav" });
  }
  let recorder = null, recTimer = null;
  async function geminiMic() {
    const btn = $("#micBtn");
    if (recorder) { recorder.stop(); return; }
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); } catch { toast(t("mic_denied")); return; }
    const chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    recorder.onstop = async () => {
      clearTimeout(recTimer); stream.getTracks().forEach((tr) => tr.stop());
      recorder = null; btn.classList.remove("active");
      $("#listening span:last-child").textContent = t("ai_processing");
      try {
        const fd = new FormData();
        fd.append("audio", await toWav(new Blob(chunks, { type: chunks[0] ? chunks[0].type : "audio/webm" })), "voice.wav");
        const r = await api("/api/voice", fd);
        const input = $("#farmerInput");
        if (r.transcript) input.value = (input.value ? input.value.trim() + " " : "") + r.transcript;
        S.ai = r.ai; applyModifiers(r.modifiers, r.ai); renderAiBox();
      } catch { toast(t("ai_fail")); }
      $("#listening").classList.add("hidden");
    };
    recorder.start();
    btn.classList.add("active");
    $("#listening span:last-child").textContent = t("ai_listening");
    $("#listening").classList.remove("hidden");
    recTimer = setTimeout(() => recorder && recorder.stop(), 45000);
  }

  // ---------------------------------------------------------------- photo
  async function downscale(file, max = 1280) {
    const img = await createImageBitmap(file).catch(() => null);
    if (!img) return file;
    const scale = Math.min(1, max / Math.max(img.width, img.height));
    if (scale === 1 && file.size < 1.5e6) return file;
    const c = document.createElement("canvas");
    c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
    c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
    return new Promise((r) => c.toBlob((b) => r(b || file), "image/jpeg", 0.88));
  }
  async function handlePhoto(file) {
    if (!file) return;
    if (META && !META.vision.available) { toast(t("photo_unavailable")); return; }
    S.photoUrl = URL.createObjectURL(file); S.photo = null; renderAttachments();
    const fd = new FormData();
    fd.append("photo", await downscale(file), "leaf.jpg");
    try {
      S.photo = await api("/api/photo", fd);
    } catch (e) {
      S.photoUrl = null; renderAttachments(); return;
    }
    renderAttachments();
    if (S.photo.quality.issues.length) toast(S.photo.quality.issues.map((i) => t("photo_issue_" + i)).join(" · "), 5000);
    if (S.last && !$("#view-consult").classList.contains("hidden")) runDiagnose();
  }

  // ---------------------------------------------------------------- picker
  function openSheet(id) { $("#pickerBackdrop").classList.remove("hidden"); $(id).classList.remove("hidden"); document.body.classList.add("sheet-open"); }
  function closeSheets() { $("#pickerBackdrop").classList.add("hidden"); $$(".sheet").forEach((s) => s.classList.add("hidden")); document.body.classList.remove("sheet-open"); }
  function openPicker() {
    const groups = META.symptom_groups;
    $("#pickerBody").innerHTML = groups.map((g) => `
      <div class="pick-group"><p class="eyebrow">${esc(t("group_" + g.group))}</p>
      <div class="pick-chips">${g.items.map((s) => `<button class="pick ${S.picked.has(s.id) ? "on" : ""}" data-pick="${esc(s.id)}">
        <span class="pick-main">${esc(loc(s, "label"))}</span><span class="pick-sub">${esc(other(s, "label"))}</span></button>`).join("")}</div></div>`).join("");
    updatePickedCount();
    openSheet("#picker");
  }
  const updatePickedCount = () => { $("#pickedCount").textContent = S.picked.size ? `(${S.picked.size})` : ""; };

  function openSeasonSheet() {
    const opts = [{ id: null, label: t("season_auto") }, ...META.seasons.map((s) => ({ id: s.id, label: loc(s, "name"), sub: other(s, "name") }))];
    $("#seasonOptions").innerHTML = opts.map((o) => `<button class="option ${S.season === o.id ? "on" : ""}" data-season="${o.id ?? ""}">
      <span>${esc(o.label)}</span>${o.sub ? `<small>${esc(o.sub)}</small>` : ""}</button>`).join("");
    openSheet("#seasonSheet");
  }

  // ---------------------------------------------------------------- consult
  function evidenceChips(res) {
    const items = res.evidence.map((e) => {
      const src = { text: "leaf", answer: e.present ? "check" : "x", picker: "hand", ai: "mic" }[e.source] || "leaf";
      return `<button class="ev ${e.present ? "" : "absent"}" data-ev="${esc(e.symptom_id)}" data-src="${esc(e.source)}" title="${esc(t("tap_to_remove"))}">
        ${icon(src)}<span>${esc(loc(e, "label"))}${e.present ? "" : ` — ${esc(t("evidence_absent"))}`}</span>${icon("x")}</button>`;
    });
    return items.join("") || `<p class="muted">—</p>`;
  }
  function photoSummary() {
    if (!S.photo) return "";
    const top = S.photo.ranked[0];
    const label = top.id === "healthy" ? t("photo_healthy") : `${t("photo_says")}: ${loc(top, "name")} (${pct(top.p)}%)`;
    return `<div class="photo-summary"><img src="${S.photoUrl}" alt=""><span>${esc(label)}</span></div>`;
  }
  function bars(posterior) {
    const max = Math.max(...posterior.map((p) => p.p), 0.01);
    return posterior.slice(0, 5).map((p, i) => `
      <div class="bar-row ${i === 0 ? "lead" : ""}">
        <span class="bar-name">${esc(p.id === "unknown" ? t("something_else") : loc(p, "name"))}</span>
        <span class="bar-track"><span class="bar-fill" style="width:${(p.p / max) * 100}%"></span></span>
        <span class="bar-val">${pct(p.p)}%</span>
      </div>`).join("");
  }
  function renderConsult() {
    const res = S.last;
    const cs = $("#consultContext");
    if (res.context && res.context.weather) {
      const w = res.context.weather, top = (res.context.risks || [])[0];
      cs.innerHTML = `${icon("cloud")} ${Math.round(w.temp)}°C · ${Math.round(w.rh)}%${top && top.level !== "low" ? ` · <b>${esc(t("risk_" + top.level))}</b> ${esc(loc(top, "name"))}` : ""}`;
      cs.classList.remove("hidden");
    } else cs.classList.add("hidden");
    $("#evidenceChips").innerHTML = evidenceChips(res);
    $("#photoSummary").innerHTML = photoSummary();
    const q = res.question;
    const n = S.answers.length + S.skipped.length + 1;
    $("#qProgress").innerHTML = `<span>${esc(t("question_n", { n }))}</span>` +
      `<span class="dots">${Array.from({ length: 6 }, (_, i) => `<i class="${i < n ? "on" : ""}"></i>`).join("")}</span>`;
    $("#qText").textContent = loc(q, "question");
    $("#qSub").textContent = other(q, "question");
    const named = res.posterior.filter((p) => p.id !== "unknown");
    $("#whyAsked").textContent = named.length > 1
      ? t("why_asked", { a: loc(named[0], "name"), b: loc(named[1], "name") })
      : t("why_asked_one", { a: loc(named[0] || {}, "name") });
    $("#speakQ").classList.toggle("hidden", !canSpeak());
    $("#posteriorBars").innerHTML = bars(res.posterior);
    const card = $("#questionCard"); card.classList.remove("enter"); void card.offsetWidth; card.classList.add("enter");
  }

  async function answer(a) {
    const q = S.last && S.last.question;
    if (!q) return;
    if (a === "unsure") S.skipped.push(q.symptom_id);
    else S.answers.push({ symptom_id: q.symptom_id, answer: a });
    await runDiagnose();
  }

  async function removeEvidence(id, src) {
    if (src === "text") S.textMatches = S.textMatches.map((m) => (m.symptom_id === id ? { ...m, removed: true } : m));
    else if (src === "picker") S.picked.delete(id);
    else if (src === "answer") S.answers = S.answers.filter((a) => a.symptom_id !== id);
    await runDiagnose();
  }

  // ---------------------------------------------------------------- result
  function ring(p) {
    const r = 34, c = 2 * Math.PI * r;
    return `<svg class="ring" viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="${r}" class="ring-bg"/>
      <circle cx="40" cy="40" r="${r}" class="ring-fg" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - p)}"/></svg>
      <span class="ring-val">${pct(p)}<small>%</small></span>`;
  }
  function gallery(d) {
    if (!d.images || !d.images.length) return `<div class="no-photo">${icon("leaf")}<span>${esc(t("no_photo"))}</span></div>`;
    return `<div class="gallery">${d.images.map((src) => `<img src="${esc(src)}" alt="${esc(loc(d, "name"))}" loading="lazy">`).join("")}</div>`;
  }
  function statusBadge(st) {
    if (!st || !st.status || st.status === "unknown") return "";
    const reasons = (st.reasons || []).filter((r) => r.code !== "time" || st.status !== "now");
    const why = [...reasons, ...(st.warnings || [])].map((r) => t("r_" + r.code, { v: r.value })).join(" · ");
    const when = st.window && st.status !== "now" ? " · " + fmtWhen(st.window.start) : "";
    return `<span class="st st-${esc(st.status)}" title="${esc(why)}">${esc(t("st_" + st.status))}${esc(when)}</span>${why ? `<span class="st-why">${esc(why)}</span>` : ""}`;
  }
  function fmtWhen(iso, withDate) {
    const d = new Date(iso);
    const opts = withDate ? { weekday: "short", day: "numeric", month: "short", hour: "numeric" } : { weekday: "short", hour: "numeric", minute: "2-digit" };
    return new Intl.DateTimeFormat(L === "ta" ? "ta-IN" : "en-IN", opts).format(d);
  }
  function treatmentsBlock(d, adv) {
    const order = ["organic", "cultural", "chemical"];
    const pref = store.get("tab", "organic");
    const tabs = order.filter((k) => (d.treatments[k] || []).length);
    const active = tabs.includes(pref) ? pref : tabs[0];
    const tabIcon = { organic: "sprout", chemical: "flask", cultural: "hand" };
    return `<div class="tabs" role="tablist">${order.map((k) => `<button role="tab" class="tab ${k === active ? "on" : ""}" data-tab="${k}" ${(d.treatments[k] || []).length ? "" : "disabled"}>
        ${icon(tabIcon[k])}${esc(t("tab_" + k))}<small>${(d.treatments[k] || []).length}</small></button>`).join("")}</div>
      ${order.map((k) => `<div class="tab-panel ${k === active ? "" : "hidden"}" data-panel="${k}">
        ${k === "chemical" && (d.treatments[k] || []).length ? `<p class="safety">${icon("shield")} ${esc(t("chem_safety"))}</p>` : ""}
        ${(d.treatments[k] || []).map((tr) => `
          <div class="treatment">
            <div class="tr-head"><b>${esc(loc(tr, "name"))}</b><span class="eff" title="${esc(t("efficacy"))}"><i style="width:${pct(tr.efficacy)}%"></i></span></div>
            ${adv ? `<div class="tr-status">${statusBadge(adv.suitability[tr.id])}</div>` : ""}
            ${adv && adv.harvest_safety ? phiHtml(adv.harvest_safety[tr.id]) : ""}
            ${L === "ta" ? `<p class="tr-alt">${esc(tr.name_en)}</p>` : ""}
            <p class="dose">${esc(loc(tr, "dosage"))}</p>
            ${tr.application && tr.application.group ? `<p class="grp">${esc(t("group_label"))}: ${esc(tr.application.group)}</p>` : ""}
            ${!adv && tr.application && tr.application.phi_days != null ? `<p class="grp">${esc(t("phi_label", { n: tr.application.phi_days, dn: daysText(tr.application.phi_days) }))}</p>` : ""}
            <p class="src">${esc(t("source"))}: ${esc(tr.source === "jagtap2025" ? "Jagtap et al. 2025 (Mendeley Data)" : tr.source === "general" ? (L === "ta" ? "பொது வேளாண் வழிகாட்டுதல்" : "General extension guidance") : tr.source)}</p>
          </div>`).join("") || `<p class="muted">${esc(t("no_treatment_type"))}</p>`}
      </div>`).join("")}`;
  }
  function whyBlock(r) {
    const ex = r.explanation;
    const vs = ex.versus && S.last.posterior.find((p) => p.id === ex.versus);
    const d = r.disease;
    const rows = ex.evidence.slice(0, 8).map((e) => {
      const sup = e.llr >= 0;
      let what;
      if (e.kind === "photo") what = `${icon("camera")} ${esc(t("why_photo"))}${e.photo_p != null ? ` — ${pct(e.photo_p)}%` : ""}`;
      else if (e.kind === "text") what = `${icon("leaf")} ${esc(t("why_said"))}: <q>${esc(e.phrase || "")}</q> → <b>${esc(loc(e, "label"))}</b>${e.present ? "" : ` (${esc(t("evidence_absent"))})`}`;
      else if (e.kind === "answer") what = `${icon(e.present ? "check" : "x")} ${esc(t(e.present ? "why_answer_yes" : "why_answer_no"))}: <b>${esc(loc(e, "label"))}</b>`;
      else what = `${icon("hand")} ${esc(t("why_picked"))}: <b>${esc(loc(e, "label"))}</b>`;
      const kg = e.kind !== "photo" ? `<span class="kg-note">${esc(t("why_kg", { p: pct(e.theta), d: loc(d, "name") }))}</span>` : "";
      return `<li class="${sup ? "sup" : "against"}"><span class="why-what">${what}${kg}</span>
        <span class="why-tag">${esc(t(sup ? "why_supports" : "why_against"))}</span></li>`;
    }).join("");
    return `<details class="card why" open><summary><span class="eyebrow">${esc(t("why_title"))}</span></summary>
      ${vs ? `<p class="muted">${esc(t("why_vs", { a: loc(d, "name"), b: loc(vs, "name") }))}</p>` : ""}
      <ul class="why-list">${rows}</ul></details>`;
  }
  function altCards(list) {
    return `<div class="alt-grid">${list.map((a) => `<button class="alt" data-correct="${esc(a.disease_id || a.id)}">
      ${a.image ? `<img src="${esc(a.image)}" alt="" loading="lazy">` : `<span class="alt-noimg">${icon("leaf")}</span>`}
      <span class="alt-name">${esc(loc(a, "name"))}</span><span class="alt-p">${a.probability != null ? pct(a.probability) + "%" : ""}</span></button>`).join("")}</div>`;
  }

  function renderResult() {
    const r = S.last.result;
    const d = r.disease;
    const uncertain = r.confidence === "uncertain";
    const urg = d.urgency;
    const typeBadge = `<span class="badge type-${esc(d.type)}">${esc(t("type_" + d.type))}</span>`;
    const hero = uncertain ? `
      <div class="card result-hero uncertain">
        <p class="eyebrow">${esc(t("conf_uncertain"))}</p>
        <h2 class="ta-display">${esc(t(r.p_unknown > r.probability ? "unknown_title" : "uncertain_title"))}</h2>
        <p>${esc(t("uncertain_body"))}</p>
        ${altCards([{ ...d, disease_id: d.id, probability: r.probability }, ...r.alternatives])}
        <button class="btn btn-ghost btn-block" data-feedback="rejected">${esc(t("alt_none"))}</button>
      </div>` : `
      <div class="card result-hero urg-${esc(urg)}">
        <div class="hero-top">
          <div class="hero-text">
            <p class="eyebrow">${esc(t("conf_" + r.confidence))} · ${esc(t("result_lead"))}</p>
            <h2 class="disease-name ${L === "ta" ? "ta-display" : "en-display"}">${esc(loc(d, "name"))}</h2>
            <p class="disease-alt">${esc(other(d, "name"))}</p>
            <div class="badges">${typeBadge}</div>
          </div>
          <div class="ring-wrap" title="${esc(t("probability"))}">${ring(r.probability)}</div>
        </div>
        <p class="urgency">${icon("alert")} ${esc(t("urgency_" + urg))}</p>
        <p class="summary">${esc(loc(d, "summary"))}</p>
        <p class="contagion">${esc(t(d.contagious ? "contagious" : "not_contagious"))}</p>
      </div>
      <div class="card compare" id="compareCard">
        <p class="eyebrow">${esc(t("compare_title"))}</p>
        ${gallery(d)}
        <div class="answer-row" id="confirmRow">
          <button class="btn btn-yes" data-feedback="confirmed">${icon("check")}<span>${esc(t("confirm_yes"))}</span></button>
          <button class="btn btn-no" data-show-alts>${icon("x")}<span>${esc(t("confirm_no"))}</span></button>
        </div>
        <button class="btn btn-ghost btn-block" data-feedback="unsure">${esc(t("confirm_unsure"))}</button>
        <div class="alts hidden" id="altsBox"><p class="eyebrow">${esc(t("alt_title"))}</p>${altCards(r.alternatives)}
          <button class="btn btn-ghost btn-block" data-feedback="rejected">${esc(t("alt_none"))}</button></div>
        <p class="thanks hidden" id="thanks"></p>
      </div>`;

    const checkNext = r.check_next && r.check_next.length ? `<div class="card"><p class="eyebrow">${esc(t("check_next"))}</p>
      <ul class="check-list">${r.check_next.map((c) => `<li>${esc(loc(c, "label"))}</li>`).join("")}</ul></div>` : "";

    const actions = `<div class="actions no-print">
        ${canSpeak() ? `<button class="btn btn-ghost" data-act="speak">${icon("speaker")}<span>${esc(t("action_listen"))}</span></button>` : ""}
        <button class="btn btn-ghost" data-act="share">${icon("share")}<span>${esc(t("action_share"))}</span></button>
        <button class="btn btn-ghost" data-act="print">${icon("print")}<span>${esc(t("action_print"))}</span></button>
      </div>`;
    const main = `${hero}
      ${uncertain ? "" : `<div class="card treat"><p class="eyebrow">${esc(t("treat_title"))}</p>${treatmentsBlock(d, r.advisory)}</div>`}
      ${uncertain ? "" : `<div class="card"><p class="eyebrow">${esc(t("prevent_title"))}</p><ul class="prevent">${(d["prevention_" + L] || d.prevention_en || []).map((p) => `<li>${icon("shield")}<span>${esc(p)}</span></li>`).join("")}</ul></div>`}
      ${whyBlock(r)}`;
    const side = `${actions}
      ${uncertain ? "" : advisoryCards(r, d)}
      ${uncertain ? "" : soilCard(r, d)}
      ${uncertain ? "" : calculatorCard(d)}
      ${checkNext}`;
    $("#resultBody").innerHTML = `<div class="split-grid result-grid"><div class="split-main">${main}</div><aside class="split-side">${side}</aside></div>`;
    if (S.feedbackSent) markFeedbackDone();
    updateCalc();
  }

  function treatmentById(d, id) {
    for (const k of Object.keys(d.treatments)) { const x = d.treatments[k].find((tr) => tr.id === id); if (x) return x; }
    return null;
  }
  function advisoryCards(r, d) {
    const a = r.advisory;
    if (!a) return "";
    const p = a.plan;
    let spray = "";
    if (a.weather) {
      const gw = a.general_window;
      spray = `<div class="card spray"><p class="eyebrow">${esc(t("spray_title"))}</p>${wxLine(a.weather)}
        ${a.outbreak ? outbreakLines({ diseases: [a.outbreak], radius_km: S.ctx ? S.ctx.outbreaks.radius_km : 30, days: S.ctx ? S.ctx.outbreaks.days : 21 }) : ""}
        ${a.risk && a.risk.level !== "low" ? `<p class="risk-note"><span class="lvl ${esc(a.risk.level)}">${esc(t("risk_" + a.risk.level))}</span> ${esc(loc(a.risk, "explain") || t("note_weather_favours"))}</p>` : ""}
        <p class="window ${gw && gw.in_hours === 0 ? "ok" : ""}">${icon(gw && gw.in_hours === 0 ? "check" : "clock")}
          ${esc(gw ? (gw.in_hours === 0 ? t("spray_now_ok") : t("spray_next", { when: fmtWhen(gw.start) })) : t("spray_none"))}</p></div>`;
    } else if (a.outbreak) {
      spray = `<div class="card">${outbreakLines({ diseases: [a.outbreak], radius_km: 30, days: 21 })}</div>`;
    }
    const notes = p.notes.map((n) => {
      if (n.code === "rotate") {
        const alt = n.alternative ? treatmentById(d, n.alternative) : null;
        return t("note_rotate", { p: n.product, g: n.group, alt: alt ? t("note_rotate_alt", { a: loc(alt, "name") }) : "" });
      }
      if (n.code === "wrong_product") return t("note_wrong_product", { p: n.product });
      if (n.code === "weather_favours") return `${t("note_weather_favours")}${loc(n, "explain") ? " — " + loc(n, "explain") : ""}`;
      if (n.code === "picking") return t("note_picking", { every: n.every, d: fmtDay(n.next_pick) });
      if (n.code === "phi_no_safe_option") return t("note_phi_no_safe", { n: n.phi, dn: daysText(n.phi), every: n.every });
      if (n.code === "phi_avoid") { const x = treatmentById(d, n.treatment_id); return t("note_phi_avoid", { p: x ? loc(x, "name") : n.treatment_id, n: n.phi, dn: daysText(n.phi), every: n.every }); }
      return t("note_" + n.code);
    });
    const sched = p.schedule.map((x) => {
      const tr = treatmentById(d, x.treatment_id);
      return `<li><span class="date">${esc(fmtWhen(x.date, true))}</span><span><b>${esc(tr ? loc(tr, "name") : x.treatment_id)}</b>
        <small>${esc(tr ? loc(tr, "dosage") : "")}${x.group ? " · " + esc(x.group) : ""} · ${esc(t(x.forecast_checked ? "schedule_checked" : "schedule_recheck"))}${x.after_pick ? " · " + esc(t("sched_after_pick")) : ""}${x.phi ? " · " + esc(t("sched_safe", { d: fmtDay(x.safe_from) })) : ""}</small></span></li>`;
    }).join("");
    const plan = `<div class="card plan"><p class="eyebrow">${esc(t("plan_title"))}</p>
      ${S.last.crop && S.last.crop.stage && S.last.crop.dat != null ? `<p class="crop-line">${icon("sprout")}<span>${esc(t("my_crop_line", { s: stageText(S.last.crop) }))}</span></p>` : ""}
      <p class="plan-level lvl-${esc(p.level)}">${esc(t("plan_level_" + p.level))}</p>
      ${p.scope ? `<p>${esc(t("scope_" + p.scope))}</p>` : ""}
      ${notes.length ? `<ul class="notes">${notes.map((n) => `<li>${icon("alert")}<span>${esc(n)}</span></li>`).join("")}</ul>` : ""}
      ${sched ? `<p class="eyebrow" style="margin-top:12px">${esc(t("schedule_title"))}</p><ol class="schedule">${sched}</ol>
        <button class="btn btn-ghost btn-sm" data-act="ics">${icon("clock")}<span>${esc(t("add_calendar"))}</span></button>` : ""}
    </div>`;
    return spray + plan;
  }
  function calculatorCard(d) {
    const items = Object.values(d.treatments).flat().filter((x) => x.application && x.application.dose);
    if (!items.length) return "";
    const c = { ...store.get("calc", { tank: 16, area: 50, unit: "cents", vol: 200 }),
      ...(S.field && S.field.area ? { area: S.field.area, unit: S.field.unit } : {}) };
    return `<div class="card calc" id="calcCard"><p class="eyebrow">${esc(t("calc_title"))}</p>
      <div class="calc-in">
        <label>${esc(t("calc_tank"))}<select data-calc="tank">${[10, 15, 16, 20].map((v) => `<option value="${v}" ${+c.tank === v ? "selected" : ""}>${v} L</option>`).join("")}</select></label>
        <label>${esc(t("calc_area"))}<span class="pair"><input type="number" min="1" step="1" data-calc="area" value="${esc(c.area)}">
          <select data-calc="unit"><option value="cents" ${c.unit === "cents" ? "selected" : ""}>${esc(t("calc_cents"))}</option><option value="acres" ${c.unit === "acres" ? "selected" : ""}>${esc(t("calc_acres"))}</option></select></span></label>
        <label>${esc(t("calc_volume"))}<input type="number" min="50" step="10" data-calc="vol" value="${esc(c.vol)}"></label>
      </div>
      <div id="calcOut"></div><p class="muted small">${esc(t("calc_note"))}</p></div>`;
  }
  const fmtAmt = (v, unit) => `${v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(1) : v.toFixed(2)} ${unit}`;
  function updateCalc() {
    const card = $("#calcCard");
    if (!card || !S.last || !S.last.result) return;
    const get = (k) => $(`[data-calc=${k}]`, card).value;
    const c = { tank: +get("tank"), area: Math.max(0, +get("area")), unit: get("unit"), vol: Math.max(1, +get("vol")) };
    store.set("calc", c);
    const acres = c.unit === "cents" ? c.area / 100 : c.area;
    const water = acres * c.vol;
    const tanks = Math.max(1, Math.ceil(water / c.tank));
    const d = S.last.result.disease;
    const items = Object.values(d.treatments).flat().filter((x) => x.application && x.application.dose);
    $("#calcOut").innerHTML = `<table class="calc-table"><thead><tr><th></th><th>${esc(t("calc_per_tank"))}</th><th>${esc(t("calc_total"))}</th></tr></thead><tbody>
      ${items.map((x) => {
        const ds = x.application.dose, mid = (ds.min + ds.max) / 2;
        let perTank, total;
        if (ds.per === "litre") { perTank = mid * c.tank; total = mid * water; }
        else { const perAcre = ds.per === "hectare" ? mid / 2.471 : mid; total = perAcre * acres; perTank = total / tanks; }
        const range = ds.min !== ds.max && ds.per === "litre" ? ` (${fmtAmt(ds.min * c.tank, ds.unit)}–${fmtAmt(ds.max * c.tank, ds.unit)})` : "";
        return `<tr><td>${esc(loc(x, "name"))}</td><td><b>${esc(fmtAmt(perTank, ds.unit))}</b>${esc(range)}</td><td>${esc(fmtAmt(total, ds.unit))}</td></tr>`;
      }).join("")}</tbody></table>
      <p class="muted small">${esc(t("calc_tanks", { n: tanks }))} × ${c.tank} L = ${Math.round(water)} L</p>`;
  }
  function downloadIcs() {
    const d = S.last.result.disease;
    const stamp = (iso) => iso.replace(/[-:]/g, "").slice(0, 13) + "00";
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Tomato Doctor//EN"];
    S.last.result.advisory.plan.schedule.forEach((x, i) => {
      const tr = treatmentById(d, x.treatment_id);
      const end = new Date(new Date(x.date).getTime() + 3600e3);
      const endIso = `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, "0")}-${String(end.getDate()).padStart(2, "0")}T${String(end.getHours()).padStart(2, "0")}:00`;
      const esc2 = (v) => String(v).replace(/[,;\\]/g, (m) => "\\" + m);
      lines.push("BEGIN:VEVENT", `UID:${S.sessionId}-${i}@tomatodoc`, `DTSTAMP:${stamp(new Date().toISOString())}Z`,
        `DTSTART:${stamp(x.date)}`, `DTEND:${stamp(endIso)}`,
        `SUMMARY:${esc2(`${t("app_name")}: ${tr ? loc(tr, "name") : x.treatment_id}`)}`,
        `DESCRIPTION:${esc2(`${loc(d, "name")} — ${tr ? loc(tr, "dosage") : ""}. ${t("schedule_recheck")}${x.phi ? " " + t("sched_safe", { d: x.safe_from }) : ""}`)}`,
        "BEGIN:VALARM", "TRIGGER:-PT12H", "ACTION:DISPLAY", `DESCRIPTION:${esc2(t("app_name"))}`, "END:VALARM", "END:VEVENT");
    });
    lines.push("END:VCALENDAR");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\r\n")], { type: "text/calendar" }));
    a.download = "tomato-spray-plan.ics"; a.click();
  }

  function resultSpeech() {
    const r = S.last.result, d = r.disease;
    const tr = [...(d.treatments.organic || []), ...(d.treatments.cultural || []), ...(d.treatments.chemical || [])].slice(0, 2);
    return [loc(d, "name"), t("urgency_" + d.urgency), loc(d, "summary"), t("treat_title") + ": " + tr.map((x) => `${loc(x, "name")}, ${loc(x, "dosage")}`).join(". ")].join(". ");
  }
  function share() {
    const r = S.last.result, d = r.disease;
    const tr = [...(d.treatments.organic || []), ...(d.treatments.chemical || []), ...(d.treatments.cultural || [])].slice(0, 2)
      .map((x) => `${loc(x, "name")} – ${loc(x, "dosage")}`).join("; ");
    const text = t("share_text", { d: `${loc(d, "name")} / ${other(d, "name")}`, p: pct(r.probability), t: tr }) + "\n" + location.origin;
    if (navigator.share) navigator.share({ title: t("app_name"), text }).catch(() => {});
    else window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener");
  }

  async function sendFeedback(outcome, correctedTo) {
    if (S.feedbackSent) return;
    const r = S.last.result;
    try {
      await api("/api/feedback", { session_id: S.sessionId, outcome, disease_id: r.disease_id, corrected_to: correctedTo || null });
    } catch { return; }
    S.feedbackSent = true;
    updateHistoryOutcome(outcome, correctedTo);
    markFeedbackDone(outcome);
    toast(t(outcome === "confirmed" || outcome === "corrected" ? "thanks_confirm" : "thanks_reject"));
    if (outcome === "corrected" && correctedTo) setTimeout(() => navigate(`disease/${correctedTo}`), 900);
  }
  function markFeedbackDone(outcome) {
    $$("#resultBody [data-feedback], #resultBody [data-show-alts], #resultBody [data-correct]").forEach((b) => (b.disabled = true));
    const th = $("#thanks");
    if (th) { th.textContent = t(outcome === "rejected" || outcome === "unsure" ? "thanks_reject" : "thanks_confirm"); th.classList.remove("hidden"); }
  }

  // ---------------------------------------------------------------- my field (optional): crop stage + harvest
  // Same stage table as tomatodoc/crop.py (days after transplanting).
  const STAGES = [["establishment", 0], ["vegetative", 20], ["flowering", 35], ["fruiting", 55], ["harvest", 70]];
  let fieldDraft = null;
  const isoDay = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const todayIso = () => isoDay(new Date());
  const daysSince = (iso) => Math.round((new Date(todayIso()) - new Date(iso)) / 864e5);
  const addDays = (iso, n) => { const d = new Date(iso); d.setDate(d.getDate() + n); return isoDay(d); };
  const fmtDay = (iso) => new Intl.DateTimeFormat(L === "ta" ? "ta-IN" : "en-IN", { weekday: "short", day: "numeric", month: "short" }).format(new Date(iso));
  function stageOf(f) {
    if (!f || !f.planting_date) return null;
    const dat = daysSince(f.planting_date);
    if (!(dat >= 0 && dat <= 180)) return null;
    const i = STAGES.reduce((k, [, start], j) => (dat >= start ? j : k), 0);
    const nxt = STAGES[i + 1];
    return { stage: STAGES[i][0], idx: i, dat, next: nxt ? nxt[0] : null, nextIn: nxt ? nxt[1] - dat : null };
  }
  const stageText = (st) => `${t("stage_day", { n: st.dat })} · ${t("cs_" + st.stage)}`;
  const cropType = () => (S.field && S.field.crop_type) || S.crop || "variety";
  function fieldPayload() {
    const f = S.field;
    if (!f) return null;
    return { planting_date: f.planting_date || null, harvesting: f.harvesting || "auto", last_pick: f.last_pick || null,
      pick_every: f.pick_every || 4, crop_type: f.crop_type || null };
  }
  function updateFieldDot() { $("#fieldDot").classList.toggle("hidden", !S.field && !S.soil); }
  function renderFieldChip() {
    const st = stageOf(S.field);
    $("#fieldChip").classList.toggle("hidden", !st);
    if (st) $("#fieldChipLabel").textContent = t("field_chip", { s: stageText(st) });
  }
  function stageHtml(st) {
    if (!st) return `<p class="muted small">${esc(t("stage_hint"))}</p>`;
    return `<div class="stage-bar">${STAGES.map(([s], i) => `<span class="${i < st.idx ? "done" : i === st.idx ? "on" : ""}">${esc(t("cs_" + s))}</span>`).join("")}</div>
      <p class="stage-now"><b>${esc(stageText(st))}</b>${st.next ? ` — ${esc(t("stage_next", { s: t("cs_" + st.next), n: st.nextIn }))}` : ""}</p>
      <p class="muted small">${esc(t("stage_note"))}</p>`;
  }
  function renderFieldSegs() {
    $$("#cropSeg [data-crop]").forEach((b) => b.classList.toggle("on", b.dataset.crop === fieldDraft.crop_type));
    $$("#pickSeg [data-pick-mode]").forEach((b) => b.classList.toggle("on", b.dataset.pickMode === fieldDraft.harvesting));
    const st = stageOf({ planting_date: $("#plantDate").value });
    const picking = fieldDraft.harvesting === "yes" || (fieldDraft.harvesting === "auto" && st && st.stage === "harvest");
    $("#pickDetails").classList.toggle("hidden", !picking);
    $("#stageBox").innerHTML = stageHtml(st);
  }
  function renderMyField(arg) {
    const f = S.field || {};
    fieldDraft = { planting_date: f.planting_date || "", variety: f.variety || "", crop_type: f.crop_type || S.crop || "variety",
      area: f.area ?? "", unit: f.unit || "cents", harvesting: f.harvesting || "auto", last_pick: f.last_pick || "", pick_every: f.pick_every || 4 };
    $("#plantDate").value = fieldDraft.planting_date;
    $("#plantDate").max = todayIso();
    $("#lastPick").value = fieldDraft.last_pick;
    $("#lastPick").max = todayIso();
    $("#varietyName").value = fieldDraft.variety;
    $("#fieldArea").value = fieldDraft.area;
    $("#fieldUnit").value = fieldDraft.unit;
    $("#pickEvery").innerHTML = [2, 3, 4, 5, 6, 7, 10].map((n) => `<option value="${n}" ${+fieldDraft.pick_every === n ? "selected" : ""}>${esc(t("days_n", { n }))}</option>`).join("");
    $("#fieldStatePill").textContent = t(S.field ? "field_active" : "soil_optional");
    $("#fieldStatePill").classList.toggle("on", !!S.field);
    $("#fieldRemove").classList.toggle("hidden", !S.field);
    $("#fieldLocLabel").textContent = S.location ? locLabel() : t("field_loc_none");
    renderFieldSegs();
    renderSoil();
    if (arg === "soil") setTimeout(() => $("#soilSection").scrollIntoView({ behavior: "smooth", block: "start" }), 60);
  }
  function saveField() {
    const area = parseFloat($("#fieldArea").value);
    S.field = { planting_date: $("#plantDate").value || null, variety: $("#varietyName").value.trim().slice(0, 40) || null,
      crop_type: fieldDraft.crop_type, area: area > 0 ? area : null, unit: $("#fieldUnit").value,
      harvesting: fieldDraft.harvesting, last_pick: $("#lastPick").value || null, pick_every: +$("#pickEvery").value || 4 };
    store.set("field", S.field);
    updateFieldDot(); renderFieldChip();
    $("#fieldStatePill").textContent = t("field_active"); $("#fieldStatePill").classList.add("on");
    $("#fieldRemove").classList.remove("hidden");
    toast(t("field_saved"));
    if (S.location) loadContext();
    if (S.soil) loadSoilReport();
  }
  function removeField() {
    S.field = null; store.set("field", null);
    updateFieldDot(); renderFieldChip();
    toast(t("field_removed"));
    renderMyField();
    if (S.location) loadContext();
  }
  function phiHtml(ph) {
    if (!ph) return "";
    const txt = ph.phi === 0 ? t("phi_zero")
      : ph.status === "blocks_pick" ? t("phi_blocks", { n: ph.phi, d: fmtDay(ph.safe_from) })
      : ph.status === "after_pick" ? t("phi_after_pick", { n: ph.phi, d: fmtDay(ph.safe_from) })
      : t("phi_after", { n: ph.phi, dn: daysText(ph.phi), d: fmtDay(ph.safe_from) });
    return `<p class="phi phi-${esc(ph.status)}">${icon("clock")}<span>${esc(txt)}</span></p>`;
  }
  function alertsHtml(alerts) {
    if (!alerts || !alerts.length) return "";
    return alerts.map((a) => {
      const tr = a.treatment, w = a.window;
      const when = !tr ? "" : !w ? t("alert_nowindow") : w.in_hours === 0 ? t("alert_now") : t("alert_when", { when: fmtWhen(w.start) });
      return `<div class="prevent-alert"><p class="pa-title">${icon("alert")}<span>${esc(t("alert_title", { d: loc(a, "name") }))}</span></p>
        ${loc(a, "explain") ? `<p class="pa-why">${esc(loc(a, "explain"))}</p>` : ""}
        ${tr ? `<p class="pa-do"><b>${esc(t("alert_spray"))}</b> ${esc(loc(tr, "name"))} — ${esc(loc(tr, "dosage"))}</p>
          <p class="pa-when">${icon("clock")}<span>${esc(when)}</span></p>${phiHtml(tr.phi)}` : `<p class="pa-do">${esc(t("alert_cultural"))}</p>`}
        <a class="link" href="#disease/${esc(a.disease_id)}">${esc(t("alert_more"))}</a></div>`;
    }).join("");
  }

  // ---------------------------------------------------------------- soil test report (optional)
  const SOIL_MAIN = ["ph", "ec", "oc", "n", "p", "k", "zn"];
  const SOIL_MORE = ["s", "fe", "mn", "cu", "b", "ca", "mg"];
  const SOIL_UNIT = { ph: "", ec: "dS/m", oc: "%", n: "kg/ha", p: "kg/ha", k: "kg/ha", s: "ppm", zn: "ppm", fe: "ppm", mn: "ppm", cu: "ppm", b: "ppm", ca: "cmol/kg", mg: "cmol/kg" };
  const BASIS = { p: ["P", "P2O5", 0.4364], k: ["K", "K2O", 0.8301] };
  const BLANKET = { variety: [150, 100, 50], hybrid: [200, 250, 250] };
  let soilDraft = null;
  const fmtNum = (v) => (v == null ? "" : Math.abs(v) >= 100 ? String(Math.round(v)) : String(+(+v).toFixed(2)));
  function updateSoilDot() { updateFieldDot(); }
  function draftFromSoil() {
    const f = (S.soil && S.soil.form) || {};
    const raw = { ...(f.raw || {}) };
    if (S.soil && !f.raw) for (const [k, v] of Object.entries(S.soil.values || {})) raw[k] = fmtNum(v);
    return { raw, basis: { p: "P", k: "K", ...(f.basis || {}) }, texture: S.soil ? S.soil.texture : null,
      date: (S.soil && S.soil.sample_date) || "" };
  }
  function soilField(p) {
    const b = BASIS[p];
    const unit = b ? `<select data-basis="${p}" aria-label="unit">${b.slice(0, 2).map((x) =>
      `<option value="${x}" ${soilDraft.basis[p] === x ? "selected" : ""}>${x.replace("2", "₂").replace("O5", "O₅")}</option>`).join("")}</select>`
      : SOIL_UNIT[p] ? `<em>${esc(SOIL_UNIT[p])}</em>` : "";
    return `<label class="soil-field"><span>${esc(t("sp_" + p))}</span><span class="soil-in">
      <input type="number" inputmode="decimal" step="any" min="0" data-soil="${p}" value="${esc(soilDraft.raw[p] ?? "")}">${unit}</span></label>`;
  }
  function renderSoilSegs() {
    $$("#texSeg [data-tex]").forEach((b) => b.classList.toggle("on", b.dataset.tex === soilDraft.texture));
  }
  function renderSoilForm() {
    $("#soilMain").innerHTML = SOIL_MAIN.map(soilField).join("");
    $("#soilMore").innerHTML = SOIL_MORE.map(soilField).join("");
    if (SOIL_MORE.some((p) => soilDraft.raw[p] !== undefined && soilDraft.raw[p] !== "")) $("#soilMore").closest("details").open = true;
    $("#soilDate").value = /^\d{4}-\d{2}-\d{2}$/.test(soilDraft.date) ? soilDraft.date : "";
    renderSoilSegs();
  }
  async function renderSoil() {
    soilDraft = draftFromSoil();
    renderSoilForm();
    $("#soilUploadNote").textContent = t(META && META.voice_ai.available ? "soil_upload_ai" : "soil_upload_noai");
    $("#soilStatePill").textContent = t(S.soil ? "soil_active" : "soil_optional");
    $("#soilStatePill").classList.toggle("on", !!S.soil);
    $("#soilRemove").classList.toggle("hidden", !S.soil);
    $("#soilStatus").classList.add("hidden");
    $("#soilReport").innerHTML = "";
    if (S.soil) await loadSoilReport();
  }
  function readSoilForm() {
    $$("[data-soil]").forEach((el) => { soilDraft.raw[el.dataset.soil] = el.value.trim(); });
    $$("[data-basis]").forEach((el) => { soilDraft.basis[el.dataset.basis] = el.value; });
    soilDraft.date = $("#soilDate").value;
    const values = {};
    for (const [p, v] of Object.entries(soilDraft.raw)) {
      if (v === "" || v == null || isNaN(+v) || +v < 0) continue;
      const b = BASIS[p];
      values[p] = b && soilDraft.basis[p] === b[1] ? +(+v * b[2]).toFixed(2) : +v;
    }
    return { values, texture: soilDraft.texture, sample_date: soilDraft.date || null,
      form: { raw: { ...soilDraft.raw }, basis: { ...soilDraft.basis } } };
  }
  async function saveSoil(quiet) {
    const soil = readSoilForm();
    if (!Object.keys(soil.values).length && !soil.texture) { toast(t("soil_empty")); return false; }
    S.soil = soil;
    store.set("soil", S.soil);
    updateSoilDot();
    $("#soilStatePill").textContent = t("soil_active"); $("#soilStatePill").classList.add("on");
    $("#soilRemove").classList.remove("hidden");
    if (!quiet) toast(t("soil_saved"));
    await loadSoilReport(true);
    return true;
  }
  function removeSoil() {
    S.soil = null; store.set("soil", null); updateSoilDot();
    toast(t("soil_removed"));
    renderSoil();
  }
  async function loadSoilReport(scroll) {
    let sum;
    try { sum = await api("/api/soil", { soil: S.soil, crop_type: cropType() }, { quiet: true }); } catch { return; }
    $("#soilReport").innerHTML = soilReportHtml(sum);
    if (scroll) $("#soilReport").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function soilStatus(msg, kind) {
    const el = $("#soilStatus");
    el.className = `soil-status ${kind || ""}`;
    el.innerHTML = kind === "busy" ? `<span class="pulse"></span><span>${esc(msg)}</span>` : esc(msg);
  }
  async function uploadSoilReport(file) {
    if (!file) return;
    const isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
    soilStatus(t("soil_reading"), "busy");
    const fd = new FormData();
    if (isPdf) fd.append("report", new Blob([file], { type: "application/pdf" }), "report.pdf");
    else fd.append("report", await downscale(file, 2000), "report.jpg");
    let r;
    try { r = await api("/api/soil/report", fd, { quiet: true }); } catch (e) {
      const code = e.message;
      soilStatus(t(e.status === 503 ? "soil_read_needs_ai" : code === "not_a_soil_report" ? "soil_read_not_report"
        : code === "no_values" ? "soil_read_none" : "soil_read_fail"), "bad");
      return;
    }
    soilDraft = { ...soilDraft, raw: {}, basis: { p: "P", k: "K" } };
    for (const [k, v] of Object.entries(r.soil.values)) soilDraft.raw[k] = fmtNum(v);
    if (r.soil.texture) soilDraft.texture = r.soil.texture;
    const dm = String(r.soil.sample_date || "").match(/(\d{1,2})[./-](\d{1,2})[./-](\d{4})/);
    if (dm) soilDraft.date = `${dm[3]}-${dm[2].padStart(2, "0")}-${dm[1].padStart(2, "0")}`;
    renderSoilForm();
    $$("[data-soil]").forEach((el) => el.classList.toggle("filled", el.value !== ""));
    if (await saveSoil(true)) soilStatus(t("soil_read_ok", { n: r.found }), "ok");
  }
  function soilActionText(a, vals, diseaseName) {
    return t("sa_" + a.code, { ph: fmtNum(vals.ph), ec: fmtNum(vals.ec), oc: vals.oc != null ? ` (${fmtNum(vals.oc)}%)` : "", d: diseaseName || "" });
  }
  function planHtml(plan) {
    const base = BLANKET[plan.crop] || BLANKET.variety;
    const rows = plan.products.map((x) => `<tr><td>${esc(t("fert_" + x.product))}</td><td>${x.basal_kg} kg</td>
      <td>${x.top_kg ? `${x.top_kg} kg` : "—"}</td><td><b>${x.kg_acre} kg</b></td></tr>`).join("");
    const npk = ["n", "p", "k"].map((e) => {
      const n = plan.nutrients[e];
      return `<span class="chip npk ${n.rating ? "r-" + n.rating : ""}">${e.toUpperCase()}: ${esc(n.rating ? t("sr_" + n.rating) : t("soil_plan_standard"))}${n.factor !== 1 ? ` · ${n.factor > 1 ? "+" : "−"}${Math.round(Math.abs(n.factor - 1) * 100)}%` : ""}</span>`;
    }).join("");
    const micros = plan.micros.map((m) => `<li>${icon("sprout")}<span><b>${esc(t("fert_" + m.product))}</b> — ${m.element === "s" ? esc(t("plan_micro_s"))
      : [m.kg_acre ? t("plan_micro_soil", { kg: m.kg_acre }) : "", m.foliar_g_l ? t("plan_micro_foliar", { g: m.foliar_g_l }) : ""].filter(Boolean).map(esc).join(" ")}</span></li>`).join("");
    const pd = S.field && S.field.planting_date;
    return `<div class="chips npk-row">${npk}</div>
      <table class="calc-table plan-table"><thead><tr><th></th><th>${esc(t("plan_basal"))}</th><th>${esc(pd ? t("plan_top_date", { d: fmtDay(addDays(pd, 30)) }) : t("plan_top", { d: 30 }))}</th><th>${esc(t("calc_total"))}</th></tr></thead><tbody>${rows}</tbody></table>
      <ul class="notes plan-extra"><li>${icon("leaf")}<span>${esc(t("plan_fym", { t: Math.round(plan.fym_t_acre) }))}</span></li>${micros}</ul>
      <p class="muted small">${esc(t("soil_plan_note", { crop: t("crop_" + plan.crop), n: base[0], p: base[1], k: base[2] }))}</p>`;
  }
  function soilReportHtml(sum) {
    const it = sum.interpretation;
    const vals = Object.fromEntries(it.params.map((p) => [p.param, p.value]));
    const rows = it.params.map((r) => `<li class="sr-row"><span class="sr-name">${esc(t("sp_" + r.param))}</span>
      <span class="sr-val">${esc(fmtNum(r.value))} <small>${esc(r.unit)}</small></span><span class="sr-pill ${esc(r.status)}">${esc(t("sr_" + r.rating))}</span></li>`).join("");
    const tex = it.texture ? `<p class="muted small">${esc(t("soil_texture"))}: <b>${esc(t("tex_" + it.texture))}</b></p>` : "";
    const risks = sum.risks.map((r) => `<a class="risk-row" href="#disease/${esc(r.disease_id)}">
      <span class="lvl ${r.factor >= 1.5 ? "high" : "medium"}">${esc(t(r.factor >= 1.5 ? "risk_high" : "risk_medium"))}</span>
      <span class="risk-name">${esc(loc(r, "name"))}<small>${esc(r.reasons.map((x) => t("sw_" + x)).join(", "))}</small></span><span></span></a>`).join("");
    const fixes = sum.general.map((a) => `<li>${icon("soil")}<span>${esc(soilActionText(a, vals))}</span></li>`).join("");
    return `<div class="card"><p class="eyebrow">${esc(t("soil_health"))}</p><ul class="sr-list">${rows}</ul>${tex}
        <p class="muted small">${esc(t("soil_rating_src"))}</p></div>
      ${risks ? `<div class="card"><p class="eyebrow">${esc(t("soil_risks"))}</p><div class="risk-list">${risks}</div></div>` : ""}
      <div class="card"><p class="eyebrow">${esc(t("soil_fixes"))}</p>${fixes ? `<ul class="notes soil-notes">${fixes}</ul>` : `<p class="muted">${esc(t("soil_no_issues"))}</p>`}</div>
      <div class="card"><p class="eyebrow">${esc(t("soil_plan"))}</p>${planHtml(sum.plan)}</div>
      ${S.last && S.last.status === "result" ? `<button class="btn btn-primary btn-block" data-act="soil-apply">${icon("send")}<span>${esc(t("soil_apply"))}</span></button>` : ""}`;
  }
  function soilCard(r, d) {
    const s = r.advisory && r.advisory.soil;
    if (!s) return `<a class="soil-cta no-print" href="#field/soil">${icon("soil")}<span>${esc(t("soil_add_cta"))}</span>${icon("send")}</a>`;
    const vals = Object.fromEntries(s.interpretation.params.map((p) => [p.param, p.value]));
    const flagged = s.interpretation.params.filter((p) => p.status !== "ok");
    return `<div class="card soil-card"><div class="card-head"><p class="eyebrow">${icon("soil")} ${esc(t("soil_card_title"))}</p>
        <a class="link" href="#field/soil">${esc(t("soil_view_full"))}</a></div>
      <p class="muted small">${esc(t("soil_used_note"))}${S.soil && S.soil.sample_date ? ` (${esc(S.soil.sample_date)})` : ""}</p>
      ${flagged.length ? `<div class="chips">${flagged.map((p) => `<span class="chip sr-chip ${esc(p.status)}">${esc(t("sp_" + p.param))} ${esc(fmtNum(p.value))} · ${esc(t("sr_" + p.rating))}</span>`).join("")}</div>` : ""}
      ${s.prior.length ? `<p class="soil-prior">${icon("alert")}<span>${esc(t("soil_prior", { r: s.prior.map((x) => t("sw_" + x)).join(", ") }))}</span></p>` : ""}
      ${s.actions.length ? `<ul class="notes soil-notes">${s.actions.map((a) => `<li>${icon("soil")}<span>${esc(soilActionText(a, vals, loc(d, "name")))}</span></li>`).join("")}</ul>` : ""}
      <details class="more soil-plan"><summary>${esc(t("soil_plan"))}</summary>${planHtml(s.plan)}</details></div>`;
  }

  // ---------------------------------------------------------------- library
  let libFilter = "all";
  function renderLibrary() {
    const types = ["all", ...new Set(META.diseases.map((d) => d.type))];
    $("#libraryFilters").innerHTML = types.map((ty) => `<button class="chip ${libFilter === ty ? "on" : ""}" data-filter="${ty}">${esc(ty === "all" ? t("filter_all") : t("type_" + ty))}</button>`).join("");
    $("#libraryGrid").innerHTML = META.diseases.filter((d) => libFilter === "all" || d.type === libFilter).map((d) => `
      <a class="disease-tile" href="#disease/${esc(d.id)}">
        ${d.image ? `<img src="${esc(d.image)}" alt="" loading="lazy">` : `<span class="tile-noimg type-${esc(d.type)}">${icon("leaf")}</span>`}
        <span class="tile-name">${esc(loc(d, "name"))}</span>
        <span class="tile-sub">${esc(t("type_" + d.type))}</span>
      </a>`).join("");
  }
  async function openDisease(id) {
    let d;
    try { d = await api(`/api/disease/${encodeURIComponent(id)}`); } catch { return navigate("library"); }
    const detailHtml = `<div class="split-grid"><div class="split-main">
      <div class="card result-hero urg-${esc(d.urgency)}">
        <h2 class="disease-name ${L === "ta" ? "ta-display" : "en-display"}">${esc(loc(d, "name"))}</h2>
        <p class="disease-alt">${esc(other(d, "name"))}</p>
        <div class="badges"><span class="badge type-${esc(d.type)}">${esc(t("type_" + d.type))}</span></div>
        <p class="urgency">${icon("alert")} ${esc(t("urgency_" + d.urgency))}</p>
        <p class="summary">${esc(loc(d, "summary"))}</p>
        <p class="contagion">${esc(t(d.contagious ? "contagious" : "not_contagious"))}</p>
      </div>
      <div class="card">${gallery(d)}</div>
      <div class="card treat"><p class="eyebrow">${esc(t("treat_title"))}</p>${treatmentsBlock(d)}</div>
      </div><aside class="split-side">
      <div class="card"><p class="eyebrow">${esc(t("symptoms_title"))}</p>
        <ul class="sym-list">${d.symptoms.map((s) => `<li><span>${esc(loc(s, "label"))}</span><span class="sym-bar"><i style="width:${pct(s.theta)}%"></i></span></li>`).join("")}</ul></div>
      <div class="card"><p class="eyebrow">${esc(t("prevent_title"))}</p><ul class="prevent">${(d["prevention_" + L] || []).map((p) => `<li>${icon("shield")}<span>${esc(p)}</span></li>`).join("")}</ul></div>
      <p class="muted small cite">${esc(t("source"))}: ${esc(d.source_citation || "")}</p>
      </aside></div>`;
    $("#diseaseBody").innerHTML = detailHtml;
    show("disease");
  }

  // ---------------------------------------------------------------- history
  function saveHistory() {
    const r = S.last.result, d = r.disease;
    const h = store.get("history", []).filter((x) => x.id !== S.sessionId);
    h.unshift({ id: S.sessionId, at: Date.now(), disease: d.id, name_ta: d.name_ta, name_en: d.name_en, p: r.probability, conf: r.confidence, text: S.text, outcome: null });
    store.set("history", h.slice(0, 50));
  }
  function updateHistoryOutcome(outcome, correctedTo) {
    const h = store.get("history", []);
    const e = h.find((x) => x.id === S.sessionId);
    if (e) { e.outcome = outcome; if (correctedTo) e.corrected = correctedTo; store.set("history", h); }
  }
  function renderHistory() {
    const h = store.get("history", []);
    if (!h.length) { $("#historyList").innerHTML = `<p class="muted">${esc(t("history_empty"))}</p>`; return; }
    const fmt = new Intl.DateTimeFormat(L === "ta" ? "ta-IN" : "en-IN", { dateStyle: "medium", timeStyle: "short" });
    $("#historyList").innerHTML = `<div class="card history-list">` + h.map((x) => {
      const shown = x.corrected ? META.diseases.find((d) => d.id === x.corrected) || x : x;
      return `<a class="history-item" href="#disease/${esc(x.corrected || x.disease)}">
        <span><b>${esc(loc(shown, "name"))}</b><small>${esc(fmt.format(x.at))}${x.text ? " · " + esc(x.text.slice(0, 60)) : ""}</small></span>
        <span class="hist-meta">${pct(x.p)}%${x.outcome ? `<em class="out-${esc(x.outcome)}">${esc(t("outcome_" + x.outcome) || "")}</em>` : ""}</span></a>`;
    }).join("") + `</div><button class="btn btn-ghost" id="clearHistory">${esc(t("history_clear"))}</button>`;
  }

  // ---------------------------------------------------------------- events
  function bind() {
    document.addEventListener("click", (e) => {
      const el = e.target.closest("button, a");
      if (!el) return;
      const d = el.dataset;
      if (d.nav) { e.preventDefault(); if (d.nav === "home") { resetConsult(); } navigate(d.nav); return; }
      if (d.example) { $("#farmerInput").value = d.example; $("#farmerInput").focus(); return; }
      if (d.answer) return answer(d.answer);
      if (d.ev) return removeEvidence(d.ev, d.src);
      if (d.pick) { el.classList.toggle("on"); S.picked.has(d.pick) ? S.picked.delete(d.pick) : S.picked.add(d.pick); updatePickedCount(); return; }
      if (d.season !== undefined) { S.season = d.season || null; store.set("season", S.season); closeSheets(); renderHome(); return; }
      if (d.removePhoto !== undefined) { S.photo = null; S.photoUrl = null; renderAttachments(); return; }
      if (d.clearPicked !== undefined) { S.picked = new Set(); renderAttachments(); return; }
      if (d.closeSheet !== undefined) return closeSheets();
      if (d.tab) {
        const box = el.closest(".card");
        $$(".tab", box).forEach((x) => x.classList.toggle("on", x === el));
        $$(".tab-panel", box).forEach((p) => p.classList.toggle("hidden", p.dataset.panel !== d.tab));
        store.set("tab", d.tab); return;
      }
      if (d.feedback) return sendFeedback(d.feedback);
      if (d.correct) {
        const r = S.last && S.last.result;
        return sendFeedback(r && r.disease_id === d.correct ? "confirmed" : "corrected", d.correct);
      }
      if (d.showAlts !== undefined) { $("#altsBox").classList.remove("hidden"); $("#confirmRow").classList.add("hidden"); $("#altsBox").scrollIntoView({ behavior: "smooth", block: "center" }); return; }
      if (d.act === "speak") return speak(resultSpeech());
      if (d.act === "share") return share();
      if (d.act === "print") return window.print();
      if (d.act === "ics") return downloadIcs();
      if (d.sev) { S.severity = S.severity === d.sev ? null : d.sev; S.sevByUser = true; renderSegs(); return; }
      if (d.ext) { const v = +d.ext; S.extent = S.extent != null && Math.abs(S.extent - v) < 1 ? null : v; S.extByUser = true; renderSegs(); return; }
      if (d.sprayDel !== undefined) { S.sprays.splice(+d.sprayDel, 1); renderSprays(); return; }
      if (d.district) { const [la, lo] = d.district.split(",").map(Number); return setLocation({ lat: la, lon: lo, src: "district", idx: +d.idx }); }
      if (d.act === "loc-pick") return openLocSheet();
      if (d.act === "loc-retry") return locate(true, true);
      if (d.tex) { soilDraft.texture = soilDraft.texture === d.tex ? null : d.tex; renderSoilSegs(); return; }
      if (d.crop) { fieldDraft.crop_type = d.crop; renderFieldSegs(); return; }
      if (d.pickMode) { fieldDraft.harvesting = d.pickMode; renderFieldSegs(); return; }
      if (d.act === "soil-apply") return runDiagnose({ finish: true });
      if (d.filter) { libFilter = d.filter; renderLibrary(); return; }
      if (el.id === "clearHistory") { store.set("history", []); renderHistory(); }
    });
    $("#startBtn").addEventListener("click", startDiagnosis);
    $("#farmerInput").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) startDiagnosis(); });
    $("#photoBtn").addEventListener("click", () => $("#photoInput").click());
    $("#photoInput").addEventListener("change", (e) => { handlePhoto(e.target.files[0]); e.target.value = ""; });
    $("#pickBtn").addEventListener("click", openPicker);
    $("#addSymptomsBtn").addEventListener("click", openPicker);
    $("#pickerClose").addEventListener("click", closeSheets);
    $("#pickerBackdrop").addEventListener("click", closeSheets);
    $("#pickerDone").addEventListener("click", () => {
      closeSheets(); renderAttachments();
      if (S.last && !$("#view-consult").classList.contains("hidden")) runDiagnose();
    });
    $("#seasonChip").addEventListener("click", openSeasonSheet);
    $("#locChip").addEventListener("click", openLocSheet);
    $("#gpsBtn").addEventListener("click", gps);
    $("#locClear").addEventListener("click", () => { S.location = null; S.ctx = null; S.locState = null; store.set("location", null); closeSheets(); renderHome(); });
    $("#fieldBack").addEventListener("click", () => navigate(["result", "library", "history"].includes(S.prevView) ? S.prevView : "home"));
    $("#fieldSave").addEventListener("click", saveField);
    $("#fieldRemove").addEventListener("click", removeField);
    $("#plantDate").addEventListener("change", renderFieldSegs);
    $("#pickedToday").addEventListener("click", (e) => { e.preventDefault(); $("#lastPick").value = todayIso(); });
    $("#soilUploadBtn").addEventListener("click", () => $("#soilFile").click());
    $("#soilFile").addEventListener("change", (e) => { uploadSoilReport(e.target.files[0]); e.target.value = ""; });
    $("#soilSave").addEventListener("click", () => saveSoil());
    $("#soilRemove").addEventListener("click", removeSoil);
    $("#sprayAdd").addEventListener("click", (e) => {
      e.preventDefault();
      const v = $("#sprayProduct").value.trim();
      if (!v) return;
      S.sprays.push({ product: v, days_ago: +$("#sprayDays").value });
      $("#sprayProduct").value = ""; renderSprays();
    });
    document.addEventListener("input", (e) => { if (e.target.closest("#calcCard")) updateCalc(); });
    document.addEventListener("change", (e) => { if (e.target.closest("#calcCard")) updateCalc(); });
    $("#finishBtn").addEventListener("click", () => runDiagnose({ finish: true }));
    $("#speakQ").addEventListener("click", () => S.last && S.last.question && speak(loc(S.last.question, "question")));
    $("#langToggle").addEventListener("click", () => { L = L === "ta" ? "en" : "ta"; store.set("lang", L); applyI18n(); applyTheme(); route(); });
    $("#themeBtn").addEventListener("click", () => {
      const cur = store.get("theme", "auto");
      store.set("theme", THEMES[(THEMES.indexOf(cur) + 1) % THEMES.length]);
      applyTheme();
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSheets(); });
    window.addEventListener("hashchange", route);
    const net = () => $("#offlineBanner").classList.toggle("hidden", navigator.onLine);
    window.addEventListener("online", net); window.addEventListener("offline", net); net();
    if (window.speechSynthesis) speechSynthesis.onvoiceschanged = () => { if (S.last) route(); };
  }

  // ---------------------------------------------------------------- boot
  async function boot() {
    applyI18n();
    applyTheme();
    bind();
    try { META = await api("/api/meta", null, { quiet: true }); } catch { toast(t("offline")); return; }
    setupMic();
    if (S.location) loadContext();
    autoLocate();
    updateSoilDot();
    if (!META.vision.available) $("#photoBtn").classList.add("hidden");
    if (location.hash && !/^#(library|disease|history)/.test(location.hash)) history.replaceState(null, "", location.pathname);
    route();
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
  boot();
})();
