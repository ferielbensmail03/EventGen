/* EventGen — studio frontend.
   Talks only to the real backend (server.py). No generated text is hard-coded:
   descriptions shown in the UI always come from /api/generate. */
(() => {
  "use strict";

  // ------------------------------------------------------------------ helpers
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("eventgen:" + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem("eventgen:" + k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
  };
  const fmt = {
    int: (v) => (v == null ? null : Number(v).toLocaleString("en-US")),
    num: (v, d = 2) => (v == null || Number.isNaN(Number(v)) ? null : Number(v).toFixed(d)),
    params: (v) => (v == null ? null : (v / 1e6).toFixed(1) + "M"),
    mins: (s) => (s == null ? null : s < 90 ? Math.round(s) + " s" : (s / 60).toFixed(1) + " min"),
  };
  const na = (v) => (v == null ? '<span class="na">Not available</span>' : esc(v));
  const sound = (n) => window.EGSound && window.EGSound.play(n);
  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const reducedMotion = () => motionQuery.matches || document.documentElement.classList.contains("reduce-motion");

  async function api(path, body) {
    const opt = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    let res;
    try { res = await fetch(path, opt); }
    catch { throw new Error("Cannot reach the EventGen server. Is server.py running?"); }
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON */ }
    if (!res.ok) throw new Error((data && data.error) || `Server error (${res.status}).`);
    return data;
  }

  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 2600);
  }

  // ------------------------------------------------------------------ icons
  const I = {
    concert: '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    workshop: '<path d="M14.7 6.3a4 4 0 00-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    festival: '<path d="M4 21l4-14 4 14M8 7V3M16 21l4-10M3 21h18"/><path d="M15 3l1 2 2 .5-1.5 1.5.5 2-2-1-2 1 .5-2L12 5.5l2-.5z"/>',
    exhibition: '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 15l5-5 4 4 3-3 6 6M8 21h8"/><circle cx="16" cy="8" r="1.5"/>',
    conference: '<path d="M12 3a3 3 0 013 3v5a3 3 0 01-6 0V6a3 3 0 013-3z"/><path d="M5 11a7 7 0 0014 0M12 18v3M8 21h8"/>',
    market: '<path d="M3 9l2-5h14l2 5M3 9h18v2a3 3 0 01-6 0 3 3 0 01-6 0 3 3 0 01-6 0z"/><path d="M5 13v8h14v-8M10 21v-5h4v5"/>',
    sports: '<circle cx="12" cy="12" r="9"/><path d="M12 3c2.5 3 2.5 15 0 18M3 12h18M5.5 6c4 2 9 2 13 0M5.5 18c4-2 9-2 13 0"/>',
    cultural: '<path d="M3 21h18M5 21V10M9 21V10M15 21V10M19 21V10M2 10l10-6 10 6z"/>',
    other: '<circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/>',
    hike: '<path d="M3 20l6-10 4 6 3-4 5 8z"/><circle cx="17" cy="5" r="2"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 012-2h10"/>',
    check: '<path d="M5 12l5 5 9-10"/>',
    download: '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
    regen: '<path d="M4 12a8 8 0 0114-5.3L20 9M20 4v5h-5M20 12a8 8 0 01-14 5.3L4 15M4 20v-5h5"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    spark: '<path d="M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/>',
  };
  const svg = (name, cls = "") => `<svg viewBox="0 0 24 24" aria-hidden="true" class="${cls}">${I[name]}</svg>`;

  // ------------------------------------------------------------------ static content
  const CATS = [
    { id: "concert", name: "Concert", sub: "concert · musique", labels: ["concert", "musique"] },
    { id: "workshop", name: "Workshop", sub: "atelier", labels: ["atelier"] },
    { id: "festival", name: "Festival", sub: "festival", labels: ["festival"] },
    { id: "exhibition", name: "Exhibition", sub: "exposition", labels: ["exposition"] },
    { id: "conference", name: "Conference", sub: "conférence", labels: ["conférence"] },
    { id: "market", name: "Market", sub: "marché", labels: ["marché"] },
    { id: "sports", name: "Sports event", sub: "événement sportif", labels: ["événement sportif"] },
    { id: "cultural", name: "Cultural event", sub: "événement culturel", labels: ["événement culturel"] },
    { id: "other", name: "Other", sub: "choose labels next", labels: [] },
  ];
  // Example *inputs* only. The blurb is gallery copy, never presented as model output.
  const EXAMPLES = [
    { title: "Concert de jazz au jardin", types: ["concert", "musique"], cat: "Concert", icon: "concert",
      blurb: "An open-air jazz set among the flower beds on a summer evening.", hues: ["#4c1d95", "#f59e0b"] },
    { title: "Marché de Noël artisanal", types: ["marché", "vente"], cat: "Market", icon: "market",
      blurb: "Wooden stalls, local crafts and mulled wine in the village square.", hues: ["#7f1d1d", "#fde68a"] },
    { title: "Atelier cuisine pour les enfants", types: ["atelier", "jeune public"], cat: "Workshop", icon: "workshop",
      blurb: "Young chefs learn simple seasonal recipes with a local cook.", hues: ["#065f46", "#fdba74"] },
    { title: "Exposition de peintures contemporaines", types: ["exposition", "arts visuels"], cat: "Exhibition", icon: "exhibition",
      blurb: "A gallery show of contemporary painters from the region.", hues: ["#1e3a8a", "#f472b6"] },
    { title: "Randonnée nocturne aux flambeaux", types: ["randonnée", "événement sportif"], cat: "Sports event", icon: "hike",
      blurb: "A torch-lit night walk through forest trails under the stars.", hues: ["#0f172a", "#fb923c"] },
    { title: "Vide-grenier du printemps", types: ["vide-grenier", "vente"], cat: "Market", icon: "market",
      blurb: "Neighbours sell treasures and second-hand finds on a spring Sunday.", hues: ["#14532d", "#a3e635"] },
  ];
  const PHASES = ["Analyzing event information…", "Encoding the event…", "Generating the next words…", "Polishing the story…"];

  // ------------------------------------------------------------------ state
  const state = {
    meta: null, results: null, step: 1,
    title: "", types: [], otherCat: false,
    model: store.get("model", "attention"), method: store.get("method", "beam"),
    beam: store.get("beam", 3), maxLen: store.get("maxLen", 60), ngram: store.get("ngram", 3),
    unseen: null, lossModel: null, metricDecoding: "beam",
  };
  const orderTypes = (arr) => [...new Set(arr)].sort((a, b) => a.startsWith("événement") - b.startsWith("événement"));

  // ================================================================== ROUTER
  const VIEWS = ["create", "examples", "compare", "results", "how"];
  let currentView = null;
  function route() {
    const name = (location.hash || "#create").slice(1);
    showView(VIEWS.includes(name) ? name : "create");
  }
  function showView(name) {
    if (name === currentView) return;
    const first = currentView === null;
    currentView = name;
    $$(".view").forEach((v) => {
      const on = v.dataset.view === name;
      v.hidden = !on;
      v.classList.toggle("enter", on && !first);
    });
    $$(".nav-links a").forEach((a) => { if (a.dataset.route === name) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    moveIndicator();
    closeMenu();
    if (!first) { sound("transition"); window.scrollTo({ top: 0, behavior: reducedMotion() ? "auto" : "smooth" }); $("#main").focus({ preventScroll: true }); }
    if (name === "results") renderResults();
    if (name === "compare") renderCompareBar();
    if (name === "examples" && !state.unseen) drawUnseen();
  }
  function moveIndicator() {
    const a = $(".nav-links a[aria-current='page']"), ind = $(".nav-indicator");
    if (!a || !ind) return;
    ind.style.left = a.offsetLeft + "px"; ind.style.width = a.offsetWidth + "px";
  }
  window.addEventListener("hashchange", route);
  window.addEventListener("resize", moveIndicator);

  // mobile menu
  const menuBtn = $("#menuBtn"), navLinks = $("#navLinks");
  function closeMenu() { navLinks.classList.remove("open"); menuBtn.setAttribute("aria-expanded", "false"); }
  menuBtn.addEventListener("click", () => {
    const open = !navLinks.classList.contains("open");
    navLinks.classList.toggle("open", open); menuBtn.setAttribute("aria-expanded", String(open)); sound("click");
  });
  window.addEventListener("scroll", () => $("#nav").classList.toggle("scrolled", scrollY > 8), { passive: true });

  // ================================================================== SETTINGS + SOUND
  const settingsBtn = $("#settingsBtn"), panel = $("#settingsPanel");
  function togglePanel(open) {
    panel.hidden = !open; settingsBtn.setAttribute("aria-expanded", String(open));
    if (open) $("#optSound").focus();
  }
  settingsBtn.addEventListener("click", (e) => { e.stopPropagation(); togglePanel(panel.hidden); sound("click"); });
  document.addEventListener("click", (e) => { if (!panel.hidden && !panel.contains(e.target)) togglePanel(false); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { if (!panel.hidden) { togglePanel(false); settingsBtn.focus(); } closeMenu(); hideTip(); }
  });

  function applySound(on) {
    window.EGSound.setEnabled(on);
    $("#optSound").checked = on;
    const b = $("#soundBtn");
    b.setAttribute("aria-pressed", String(on));
    b.setAttribute("aria-label", on ? "Sound on. Turn sound off" : "Sound off. Turn sound on");
    store.set("sound", on);
  }
  // Sound always starts OFF on page load (no autoplay); the preference only pre-ticks ambient/volume.
  $("#soundBtn").addEventListener("click", () => { applySound(!window.EGSound.enabled); sound("select"); toast(window.EGSound.enabled ? "Sound on" : "Sound off"); });
  $("#optSound").addEventListener("change", (e) => { applySound(e.target.checked); sound("select"); });
  $("#optAmbient").checked = store.get("ambient", false);
  window.EGSound.setAmbient($("#optAmbient").checked);
  $("#optAmbient").addEventListener("change", (e) => {
    window.EGSound.setAmbient(e.target.checked); store.set("ambient", e.target.checked);
    if (e.target.checked && !window.EGSound.enabled) applySound(true);
  });
  $("#optVolume").value = store.get("volume", 45);
  window.EGSound.setVolume($("#optVolume").value / 100);
  $("#optVolume").addEventListener("input", (e) => { window.EGSound.setVolume(e.target.value / 100); store.set("volume", +e.target.value); });
  $("#optMotion").checked = store.get("motion", false) || motionQuery.matches;
  document.documentElement.classList.toggle("reduce-motion", $("#optMotion").checked);
  $("#optMotion").addEventListener("change", (e) => {
    document.documentElement.classList.toggle("reduce-motion", e.target.checked); store.set("motion", e.target.checked); particles.reset();
  });
  document.addEventListener("click", (e) => { if (e.target.closest("[data-sound='click']")) sound("click"); });

  // ================================================================== TOOLTIPS
  const tip = $("#tooltip");
  function showTip(el) {
    tip.textContent = el.dataset.tip; tip.hidden = false;
    const r = el.getBoundingClientRect(), w = tip.offsetWidth;
    tip.style.left = Math.max(12, Math.min(innerWidth - w - 12, r.left + r.width / 2 - w / 2)) + "px";
    tip.style.top = (r.top - tip.offsetHeight - 10 < 8 ? r.bottom + 10 : r.top - tip.offsetHeight - 10) + "px";
    el.setAttribute("aria-describedby", "tooltip");
  }
  function hideTip() { tip.hidden = true; }
  document.addEventListener("mouseover", (e) => { const t = e.target.closest("[data-tip]"); if (t) showTip(t); });
  document.addEventListener("mouseout", (e) => { if (e.target.closest("[data-tip]")) hideTip(); });
  document.addEventListener("focusin", (e) => { const t = e.target.closest("[data-tip]"); if (t) showTip(t); });
  document.addEventListener("focusout", (e) => { if (e.target.closest("[data-tip]")) hideTip(); });
  document.addEventListener("click", (e) => { if (e.target.closest(".tip")) e.preventDefault(); });

  // ================================================================== MAGNETIC BUTTONS
  document.addEventListener("pointermove", (e) => {
    if (reducedMotion() || e.pointerType !== "mouse") return;
    const b = e.target.closest(".magnetic");
    $$(".magnetic").forEach((m) => { if (m !== b) { m.style.setProperty("--mx", "0px"); m.style.setProperty("--my", "0px"); } });
    if (!b || b.disabled) return;
    const r = b.getBoundingClientRect();
    b.style.setProperty("--mx", ((e.clientX - r.left - r.width / 2) * 0.18).toFixed(1) + "px");
    b.style.setProperty("--my", ((e.clientY - r.top - r.height / 2) * 0.25).toFixed(1) + "px");
  });

  // ================================================================== SEGMENTED CONTROLS
  function segmented(el, value, onChange) {
    const btns = $$("button", el);
    const set = (v, user) => {
      btns.forEach((b) => { const on = b.dataset.value === String(v); b.setAttribute("aria-checked", String(on)); b.tabIndex = on ? 0 : -1; });
      placeThumb(el);
      if (user) { sound("select"); onChange(v); }
    };
    btns.forEach((b, i) => {
      b.addEventListener("click", () => set(b.dataset.value, true));
      b.addEventListener("keydown", (e) => {
        const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
        if (!d) return;
        e.preventDefault();
        const nb = btns[(i + d + btns.length) % btns.length]; nb.focus(); set(nb.dataset.value, true);
      });
    });
    set(value, false);
    return set;
  }
  function placeThumb(el) {
    const on = $("button[aria-checked='true']", el), th = $(".seg-thumb", el);
    if (!on || !th) return;
    th.style.left = on.offsetLeft + "px"; th.style.width = on.offsetWidth + "px";
  }
  window.addEventListener("resize", () => $$(".segmented").forEach(placeThumb));

  // ================================================================== STUDIO — STEP 1
  const titleInput = $("#title");
  function renderCategories() {
    $("#categories").innerHTML = CATS.map((c) =>
      `<button type="button" class="cat" data-cat="${c.id}" aria-pressed="false">${svg(c.id)}<span>${esc(c.name)}<small>${esc(c.sub)}</small></span></button>`).join("");
    $$("#categories .cat").forEach((b) => b.addEventListener("click", () => toggleCat(b.dataset.cat)));
  }
  function toggleCat(id) {
    const c = CATS.find((x) => x.id === id);
    if (id === "other") {
      state.otherCat = !state.otherCat;
      if (state.otherCat) state.types = state.types.filter((t) => !CATS.some((k) => k.labels.includes(t)));
    } else {
      state.otherCat = false;
      const on = c.labels.every((l) => state.types.includes(l));
      state.types = on ? state.types.filter((t) => !c.labels.includes(t)) : orderTypes([...state.types, ...c.labels]);
    }
    sound("select");
    syncTypes();
  }
  function syncCats() {
    $$("#categories .cat").forEach((b) => {
      const c = CATS.find((x) => x.id === b.dataset.cat);
      const on = c.id === "other" ? state.otherCat : c.labels.every((l) => state.types.includes(l));
      b.setAttribute("aria-pressed", String(on));
    });
  }
  titleInput.addEventListener("input", () => {
    state.title = titleInput.value;
    const n = titleInput.value.length;
    $("#titleCount").textContent = `${n} / 120`;
    $("#titleCount").classList.toggle("warn", n > 100);
    if (titleInput.value.trim().length >= 2) setError("");
    scheduleInspect(); renderPreview(); scheduleLive();
  });
  function setError(msg) {
    $("#titleErr").textContent = msg;
    titleInput.closest(".field").classList.toggle("invalid", !!msg);
    titleInput.setAttribute("aria-invalid", String(!!msg));
  }
  function validTitle() {
    const t = titleInput.value.trim();
    if (!t) { setError("Give your event a title — it is the main thing the model reads."); return false; }
    if (t.length < 2) { setError("The title is too short."); return false; }
    setError(""); return true;
  }

  // ================================================================== LIVE GENERATION (as you type)
  state.live = store.get("live", true);
  let liveTimer, liveSeq = 0, liveCtrl = null, liveLast = null;
  function liveModel() {
    const avail = (state.meta?.models || []).map((m) => m.name);
    const want = state.model === "both" ? "attention" : state.model;
    return avail.includes(want) ? want : avail[0];
  }
  function liveShell(inner, dot, meta) {
    const m = (state.meta?.models || []).find((x) => x.name === liveModel());
    const warn = m && m.subset
      ? `<p class="live-warn">This checkpoint was trained on only ${fmt.int(m.subset)} examples (smoke test) — expect “de de de” until full training finishes. The page picks up the new model automatically.</p>` : "";
    return `<div class="live-head"><span class="live-dot ${dot}"></span><b>Live description</b>
      <label class="live-toggle"><input type="checkbox" class="live-on" ${state.live ? "checked" : ""}> auto-generate while typing</label>
      <span class="live-meta">${esc(meta || "")}</span></div>${inner}${warn}`;
  }
  function renderLive(inner, dot, meta) {
    ["#liveMain", "#liveSide"].forEach((s) => { $(s).innerHTML = liveShell(inner, dot, meta); });
  }
  document.addEventListener("change", (e) => {
    if (!e.target.classList.contains("live-on")) return;
    state.live = e.target.checked; store.set("live", state.live); sound("select");
    if (state.live) { liveLast = null; scheduleLive(0); } else renderLive('<p class="live-text hint">Live generation is off — use “Generate my event story”.</p>', "off");
  });
  function scheduleLive(delay = 650) {
    if (!state.live) return;
    clearTimeout(liveTimer);
    const title = titleInput.value.trim();
    if (title.length < 3) { renderLive('<p class="live-text hint">Start typing an event title — the description appears here as you write.</p>', ""); return; }
    $$(".live-text").forEach((t) => t.classList.add("stale"));
    $$(".live-dot").forEach((d) => d.className = "live-dot busy");
    liveTimer = setTimeout(runLive, delay);
  }
  async function runLive() {
    const name = liveModel();
    if (!name) { renderLive('<p class="live-text hint">No trained model on the server.</p>', "off"); return; }
    const p = { title: titleInput.value.trim(), types: state.types, models: [name], method: state.method,
      beam_width: state.beam, max_len: state.maxLen, no_repeat_ngram: state.ngram };
    const key = JSON.stringify(p);
    if (key === liveLast) { $$(".live-text").forEach((t) => t.classList.remove("stale")); $$(".live-dot").forEach((d) => d.className = "live-dot"); return; }
    const seq = ++liveSeq;
    if (liveCtrl) liveCtrl.abort();
    liveCtrl = new AbortController();
    try {
      const res = await fetch("/api/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p), signal: liveCtrl.signal });
      const data = await res.json();
      if (seq !== liveSeq) return;
      if (!res.ok) throw new Error(data.error || "Generation failed");
      liveLast = key;
      const r = data.results[0];
      const words = r.text.trim().split(/\s+/).filter(Boolean);
      const d = reducedMotion() ? 0 : 22;
      const text = words.length ? words.map((w, i) => `<span class="w" style="animation-delay:${i * d}ms">${esc(w)}</span>`).join(" ") : "<em>(empty output)</em>";
      renderLive(`<p class="live-text">${text}</p>`, "",
        `${r.decoding ? `${r.label} · ${r.decoding}` : `${r.kind === "baseline" ? "Baseline" : "Attention"} · ${data.method === "beam" ? `beam ×${data.settings.beam_width}` : "greedy"}`} · ${Math.round(r.time_ms)} ms`);
    } catch (err) {
      if (err.name === "AbortError" || seq !== liveSeq) return;
      renderLive(`<p class="live-text hint">${esc(err.message)}</p>`, "off");
    }
  }

  // ================================================================== STEP 2 — labels + live tokens
  function renderAllChips() {
    const q = $("#typeSearch").value.trim().toLowerCase();
    const list = (state.meta ? state.meta.types : []).filter((t) => !q || t.includes(q));
    $("#allChips").innerHTML = list.length
      ? list.map((t) => `<button type="button" class="chip${state.types.includes(t) ? " on" : ""}" data-type="${esc(t)}" aria-pressed="${state.types.includes(t)}">${esc(t)}</button>`).join("")
      : `<span class="muted" style="font-size:.85rem">No label matches “${esc(q)}”.</span>`;
  }
  function renderSelectedChips() {
    $("#selectedChips").innerHTML = state.types.map((t) =>
      `<button type="button" class="chip on" data-type="${esc(t)}" aria-label="Remove ${esc(t)}">${esc(t)} ${svg("x")}</button>`).join("");
  }
  function toggleType(t) {
    state.types = state.types.includes(t) ? state.types.filter((x) => x !== t) : orderTypes([...state.types, t]);
    if (state.types.length) state.otherCat = false;
    sound("select"); syncTypes();
  }
  $("#allChips").addEventListener("click", (e) => { const c = e.target.closest(".chip"); if (c) toggleType(c.dataset.type); });
  $("#selectedChips").addEventListener("click", (e) => { const c = e.target.closest(".chip"); if (c) toggleType(c.dataset.type); });
  $("#typeSearch").addEventListener("input", renderAllChips);
  function syncTypes() { syncCats(); renderAllChips(); renderSelectedChips(); scheduleInspect(); renderPreview(); renderCompareBar(); scheduleLive(300); }

  let inspectTimer, inspectSeq = 0;
  function scheduleInspect() { clearTimeout(inspectTimer); inspectTimer = setTimeout(inspect, 220); }
  async function inspect() {
    const seq = ++inspectSeq;
    const title = titleInput.value.trim();
    try {
      const r = await api("/api/inspect", { title: title || "…", types: state.types });
      if (seq !== inspectSeq) return;
      $("#serialized").textContent = title ? r.serialized : r.serialized.replace(/titre : …$/, "titre : …");
      $("#tokens").innerHTML = r.tokens.map((t, i) =>
        `<span class="tok${t.known ? "" : " unk"}" style="animation-delay:${Math.min(i * 18, 400)}ms" title="${t.known ? "in vocabulary" : "unknown → <unk>"}">${esc(t.t)}</span>`).join("");
    } catch (err) { $("#tokens").innerHTML = `<span class="muted" style="font-size:.8rem">${esc(err.message)}</span>`; }
  }

  // ================================================================== STEP 3 — model + decoding
  function renderModelCards() {
    const avail = new Set((state.meta?.models || []).map((m) => m.name));
    const opts = [
      { v: "attention", name: "Attention", badge: '<span class="badge">recommended</span>', d: "LSTM + Bahdanau attention. Looks back at every input word while writing.", need: ["attention"] },
      { v: "baseline", name: "Baseline", badge: '<span class="badge cyan">reference</span>', d: "Plain LSTM encoder–decoder with a single fixed context vector.", need: ["baseline"] },
      { v: "both", name: "Both, side by side", badge: "", d: "Run the two networks on the same input and read them next to each other.", need: ["attention", "baseline"] },
    ];
    if (!opts.find((o) => o.v === state.model && o.need.every((n) => avail.has(n)))) {
      state.model = (opts.find((o) => o.need.every((n) => avail.has(n))) || opts[0]).v;
    }
    $("#modelCards").innerHTML = opts.map((o) => {
      const ok = o.need.every((n) => avail.has(n));
      return `<button type="button" class="mcard" role="radio" data-value="${o.v}" aria-checked="${state.model === o.v}" ${ok ? "" : "disabled"} tabindex="${state.model === o.v ? 0 : -1}">
        <span class="mname">${esc(o.name)} ${o.badge}</span><p class="mdesc">${esc(o.d)}${ok ? "" : " <em>(not trained yet)</em>"}</p></button>`;
    }).join("");
    $$("#modelCards .mcard").forEach((b, i, all) => {
      b.addEventListener("click", () => { state.model = b.dataset.value; store.set("model", state.model); sound("select"); renderModelCards(); renderPreview(); scheduleLive(200); $(`#modelCards [data-value="${state.model}"]`).focus(); });
      b.addEventListener("keydown", (e) => {
        const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key]; if (!d) return;
        e.preventDefault(); let j = i;
        do { j = (j + d + all.length) % all.length; } while (all[j].disabled && j !== i);
        all[j].click();
      });
    });
  }
  const setMethod = segmented($("#segMethod"), state.method, (v) => { state.method = v; store.set("method", v); syncBeam(); renderPreview(); renderCompareBar(); scheduleLive(200); });
  segmented($("#segNgram"), state.ngram, (v) => { state.ngram = +v; store.set("ngram", +v); renderPreview(); renderCompareBar(); scheduleLive(200); });
  function syncBeam() { $("#beamSetting").classList.toggle("disabled", state.method !== "beam"); $("#beamWidth").disabled = state.method !== "beam"; }
  function bindSlider(id, outId, key) {
    const el = $(id), out = $(outId);
    const paint = () => { el.style.setProperty("--p", ((el.value - el.min) / (el.max - el.min)) * 100 + "%"); out.textContent = el.value; };
    el.value = state[key]; paint();
    el.addEventListener("input", () => { state[key] = +el.value; store.set(key, +el.value); paint(); renderPreview(); renderCompareBar(); scheduleLive(); });
    el.addEventListener("change", () => sound("select"));
  }
  bindSlider("#beamWidth", "#beamOut", "beam");
  bindSlider("#maxLen", "#maxOut", "maxLen");
  syncBeam();

  function catIconFor(types) {
    const c = CATS.find((k) => k.labels.length && k.labels.some((l) => types.includes(l)));
    return c ? c.id : "spark";
  }
  function settingsText() {
    return `${state.method === "beam" ? `Beam search ×${state.beam}` : "Greedy"} · ${state.maxLen} tokens max · ${state.ngram ? `no-repeat ${state.ngram}-grams` : "no n-gram blocking"}`;
  }
  function modelText() { return { attention: "LSTM + Bahdanau attention", baseline: "LSTM Encoder–Decoder (baseline)", both: "Attention + baseline" }[state.model]; }
  function renderPreview() {
    const t = titleInput.value.trim();
    const ic = catIconFor(state.types);
    $("#preview").innerHTML = `<div class="pv-icon">${svg(I[ic] ? ic : "spark")}</div>
      <div><div class="pv-title">${t ? esc(t) : '<span class="muted">Untitled event</span>'}</div>
      <div class="pv-meta"><span>Type <b>${esc(state.types.join(", ") || "non précisé")}</b></span>
      <span>Model <b>${esc(modelText())}</b></span><span>Decoding <b>${esc(settingsText())}</b></span></div></div>`;
  }

  // ================================================================== STEP NAVIGATION
  function goStep(n, user = true) {
    if (n > 1 && !validTitle()) { goStep(1, false); titleInput.focus(); sound("error"); return; }
    const back = n < state.step;
    state.step = n;
    $$(".step").forEach((s) => { const on = +s.dataset.step === n; s.classList.toggle("active", on); s.classList.toggle("back", on && back); });
    $$("#stepper li").forEach((li) => {
      const k = +li.dataset.step;
      li.classList.toggle("active", k === n); li.classList.toggle("done", k < n);
      $("button", li).setAttribute("aria-current", k === n ? "step" : "false");
    });
    $("#progressBar").style.width = (n / 3) * 100 + "%";
    $("#backBtn").hidden = n === 1;
    $("#nextBtn").hidden = n === 3;
    $("#genBtn").hidden = n !== 3;
    if (n === 2) { renderAllChips(); renderSelectedChips(); inspect(); }
    if (n === 3) { renderModelCards(); renderPreview(); requestAnimationFrame(() => $$(".segmented").forEach(placeThumb)); }
    if (user) {
      const studio = $("#studio");
      if (studio.getBoundingClientRect().top < 0) studio.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" });
      const focusEl = n === 1 ? titleInput : n === 2 ? $("#typeSearch") : $("#modelCards .mcard[aria-checked='true']");
      focusEl && focusEl.focus({ preventScroll: true });
    }
  }
  $("#nextBtn").addEventListener("click", () => goStep(state.step + 1));
  $("#backBtn").addEventListener("click", () => goStep(state.step - 1));
  $$("#stepper button").forEach((b) => b.addEventListener("click", () => { sound("click"); goStep(+b.closest("li").dataset.step); }));
  titleInput.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); goStep(2); sound("click"); } });
  $("#ctaCreate").addEventListener("click", () => {
    $("#studio").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" });
    setTimeout(() => titleInput.focus({ preventScroll: true }), reducedMotion() ? 0 : 500);
  });

  // ================================================================== GENERATION
  function buildNN() {
    const layers = [4, 6, 6, 4], W = 320, H = 140, nodes = [];
    let html = '<defs><linearGradient id="edgeGrad" x1="0" x2="1"><stop offset="0" stop-color="#c4b5fd" stop-opacity="0"/><stop offset=".5" stop-color="#c4b5fd"/><stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/></linearGradient></defs>';
    layers.forEach((n, li) => {
      const x = 20 + (li * (W - 40)) / (layers.length - 1);
      nodes.push([...Array(n)].map((_, i) => [x, H / 2 + (i - (n - 1) / 2) * 22]));
    });
    let edges = "";
    for (let l = 0; l < nodes.length - 1; l++)
      nodes[l].forEach(([x1, y1]) => nodes[l + 1].forEach(([x2, y2]) => {
        const fire = Math.random() < 0.28;
        edges += `<line class="edge${fire ? " fire" : ""}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" style="animation-delay:${(Math.random() * 1.6).toFixed(2)}s"/>`;
      }));
    let dots = "";
    nodes.forEach((layer, l) => layer.forEach(([x, y], i) => {
      dots += `<circle class="node live" cx="${x}" cy="${y}" r="${l === 0 || l === 3 ? 5 : 4}" style="animation-delay:${(l * 0.35 + i * 0.08).toFixed(2)}s"/>`;
    }));
    $("#nnSvg").innerHTML = html + edges + dots;
  }

  function payload() {
    const models = state.model === "both" ? ["attention", "baseline"] : [state.model];
    return { title: titleInput.value.trim(), types: state.types, models, method: state.method,
      beam_width: state.beam, max_len: state.maxLen, no_repeat_ngram: state.ngram };
  }

  let genBusy = false;
  async function runGeneration(p) {
    if (genBusy) return;
    genBusy = true;
    const form = $("#studioForm"), stage = $("#stage");
    form.hidden = true; stage.hidden = false;
    $("#stepper").style.visibility = "hidden"; $(".progress").style.visibility = "hidden";
    $("#generating").hidden = false; $("#outputs").innerHTML = ""; $("#stageActions").hidden = true;
    const meta = state.meta?.models || [];
    $("#genMeta").innerHTML = p.models.map((m) => `<span class="pillx">${esc(meta.find((x) => x.name === m)?.label || m)}</span>`).join("") +
      `<span class="pillx">${esc(p.method === "beam" ? `Beam search · width ${p.beam_width}` : "Greedy decoding")}</span>`;
    buildNN();
    $("#studio").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" });
    let k = 0;
    const phase = $("#genPhase");
    phase.textContent = PHASES[0];
    const iv = setInterval(() => { k = Math.min(k + 1, PHASES.length - 1); phase.textContent = PHASES[k]; phase.classList.remove("swap"); void phase.offsetWidth; phase.classList.add("swap"); }, 850);
    const t0 = performance.now();
    try {
      const data = await api("/api/generate", p);
      const minShow = reducedMotion() ? 0 : 1300;           // keep the transition readable, not a flicker
      await sleep(Math.max(0, minShow - (performance.now() - t0)));
      clearInterval(iv);
      $("#generating").hidden = true;
      renderOutputs(data, p);
      sound("success");
    } catch (err) {
      clearInterval(iv);
      $("#generating").hidden = true;
      $("#outputs").className = "outputs";
      $("#outputs").innerHTML = `<div class="api-error" role="alert"><strong>Generation failed.</strong> ${esc(err.message)}</div>`;
      sound("error");
    } finally {
      $("#stageActions").hidden = false;
      genBusy = false;
    }
  }

  function renderOutputs(data, p) {
    const out = $("#outputs");
    out.className = "outputs" + (data.results.length > 1 ? " two" : "");
    out.innerHTML = data.results.map((r, idx) => storyCard(r, data, p, idx)).join("");
    $$(".story", out).forEach((card, idx) => wireStory(card, data.results[idx], data, p));
  }

  function storyCard(r, data, p) {
    const words = r.text.trim() ? r.text.trim().split(/\s+/) : [];
    const delay = reducedMotion() ? 0 : 28;
    const text = words.length
      ? words.map((w, i) => `<span class="w" style="animation-delay:${i * delay}ms">${esc(w)}</span>`).join(" ")
      : "The model produced an empty description for this input.";
    const kind = r.kind === "baseline" ? "baseline" : "attention";
    const decoding = r.decoding || (data.method === "beam" ? `Beam ×${data.settings.beam_width}` : "Greedy");
    return `<article class="story ${kind}" aria-label="Generated description — ${esc(r.label)}">
      <div class="story-head"><span class="story-kicker">${kind === "attention" ? "Attention model" : "Baseline model"}</span>
        <span class="story-model">${esc(r.label)} · ${esc(r.decoding || (data.method === "beam" ? "beam search" : "greedy"))}</span></div>
      <h3 class="story-title">${esc(p.title)}</h3>
      <p class="story-text${words.length ? "" : " empty"}">${text}</p>
      ${r.unknown.length ? `<p class="unk-note">${r.unknown.length} input word(s) never seen in training → read as &lt;unk&gt;: ${r.unknown.map(esc).join(", ")}</p>` : ""}
      <div class="story-meta">
        <span><b>${words.length}</b> words</span><span><b>${r.text.length}</b> characters</span><span><b>${r.n_tokens}</b> tokens</span>
        <span><b>${r.time_ms.toLocaleString("en-US")}</b> ms</span>
        <span>${esc(decoding)}</span>
        ${r.decoding ? "" : `<span>${data.settings.no_repeat_ngram ? `No-repeat ${data.settings.no_repeat_ngram}-grams` : "No n-gram blocking"}</span>`}
      </div>
      <div class="story-actions">
        <button class="btn btn-sm" data-act="copy">${svg("copy")} <span>Copy</span></button>
        <button class="btn btn-sm" data-act="regen">${svg("regen")} Regenerate</button>
        <button class="btn btn-sm" data-act="download">${svg("download")} Download .txt</button>
      </div>
      ${r.attention ? `<div class="heat-wrap"><button class="heat-toggle" aria-expanded="false">${svg("chevron")} Attention heatmap α(t, i)</button><div class="heat" hidden></div></div>` : ""}
    </article>`;
  }

  function wireStory(card, r, data, p) {
    $("[data-act='copy']", card).addEventListener("click", async (e) => {
      const b = e.currentTarget;
      try { await navigator.clipboard.writeText(r.text); }
      catch {
        const ta = document.createElement("textarea"); ta.value = r.text; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } finally { ta.remove(); }
      }
      b.classList.add("done"); b.innerHTML = `${svg("check")} <span>Copied</span>`; sound("select");
      setTimeout(() => { b.classList.remove("done"); b.innerHTML = `${svg("copy")} <span>Copy</span>`; }, 1800);
    });
    $("[data-act='regen']", card).addEventListener("click", () => { sound("click"); runGeneration(p); });
    $("[data-act='download']", card).addEventListener("click", () => {
      const body = `${p.title}\n\n${r.text}\n\n---\nGenerated by EventGen\nModel: ${r.label}\nDecoding: ${r.decoding || `${data.method}${data.method === "beam" ? ` (width ${data.settings.beam_width})` : ""}, max ${data.settings.max_len} tokens, no-repeat n-gram ${data.settings.no_repeat_ngram || "off"}`}\nModel input: ${data.serialized}\n`;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([body], { type: "text/plain;charset=utf-8" }));
      a.download = `eventgen-${r.kind}-${p.title.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "event"}.txt`;
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      sound("click"); toast("Description downloaded");
    });
    const ht = $(".heat-toggle", card);
    if (ht) ht.addEventListener("click", () => {
      const h = $(".heat", card), open = h.hidden;
      h.hidden = !open; ht.setAttribute("aria-expanded", String(open)); sound("click");
      if (open && !h.innerHTML) h.innerHTML = heatmap(r);
    });
  }

  function heatmap(r) {
    const src = r.source_tokens, outT = r.out_tokens;
    const head = `<tr><th></th>${src.map((s) => `<th scope="col">${esc(s)}</th>`).join("")}</tr>`;
    const rows = r.attention.map((row, t) => `<tr><th scope="row">${esc(outT[t] ?? "")}</th>${row.map((a, i) =>
      `<td style="--a:${Math.max(0.04, Math.pow(a, 0.7)).toFixed(3)}" title="${esc(outT[t])} ← ${esc(src[i])}: ${a.toFixed(3)}"></td>`).join("")}</tr>`).join("");
    return `<p>Rows: generated words. Columns: input tokens. Darker = the decoder looked more at that input word. Attention is a hint about what the model uses, not a full explanation.</p><table><thead>${head}</thead><tbody>${rows}</tbody></table>`;
  }

  $("#studioForm").addEventListener("submit", (e) => {
    e.preventDefault();
    if (!validTitle()) { goStep(1); sound("error"); return; }
    sound("click"); runGeneration(payload());
  });
  $("#regenBtn").addEventListener("click", () => runGeneration(payload()));
  $("#editBtn").addEventListener("click", () => {
    $("#stage").hidden = true; $("#studioForm").hidden = false;
    $("#stepper").style.visibility = ""; $(".progress").style.visibility = "";
    goStep(3);
  });

  // ================================================================== EXAMPLES
  function exampleArt(ex, i) {
    const [a, b] = ex.hues, id = "g" + i;
    const shapes = [
      `<circle cx="250" cy="40" r="26" fill="${b}" opacity=".85"/><path d="M0 120 Q80 80 160 110 T320 100 V150 H0z" fill="#000" opacity=".35"/>`,
      `<g fill="${b}">${[...Array(14)].map((_, k) => `<circle cx="${(k * 53) % 320}" cy="${(k * 37) % 110 + 10}" r="${(k % 3) + 1.5}" opacity="${0.4 + (k % 4) * 0.15}"/>`).join("")}</g>`,
      `<circle cx="70" cy="150" r="90" fill="${b}" opacity=".35"/><circle cx="260" cy="20" r="60" fill="${b}" opacity=".25"/>`,
      `<rect x="40" y="26" width="70" height="80" rx="6" fill="${b}" opacity=".55" transform="rotate(-6 75 66)"/><rect x="130" y="20" width="90" height="70" rx="6" fill="#fff" opacity=".18"/><rect x="236" y="34" width="56" height="70" rx="6" fill="${b}" opacity=".3"/>`,
      `<path d="M0 150 L90 60 L150 110 L210 50 L320 150z" fill="#000" opacity=".45"/>${[...Array(18)].map((_, k) => `<circle cx="${(k * 71) % 320}" cy="${(k * 29) % 60 + 6}" r="1.2" fill="#fff" opacity=".8"/>`).join("")}<circle cx="120" cy="96" r="6" fill="${b}"/><circle cx="168" cy="104" r="5" fill="${b}" opacity=".8"/>`,
      `${[...Array(6)].map((_, k) => `<path d="M${k * 60 - 20} 0 l40 0 l-20 34z" fill="${k % 2 ? b : "#fff"}" opacity=".5"/>`).join("")}<circle cx="240" cy="110" r="44" fill="${b}" opacity=".3"/>`,
    ][i % 6];
    return `<svg viewBox="0 0 320 150" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="#0b0b24"/></linearGradient></defs><rect width="320" height="150" fill="url(#${id})"/>${shapes}</svg>`;
  }
  function renderGallery() {
    $("#gallery").innerHTML = EXAMPLES.map((ex, i) => `<article class="ex">
      <div class="ex-art">${exampleArt(ex, i)}<span class="ex-ico">${svg(ex.icon)}</span></div>
      <div class="ex-body"><span class="ex-cat">${esc(ex.cat)}</span><h3 class="ex-title">${esc(ex.title)}</h3>
      <p class="ex-blurb">${esc(ex.blurb)}</p>
      <div class="ex-labels">${ex.types.map((t) => `<span class="tok">${esc(t)}</span>`).join("")}</div>
      <button class="btn btn-secondary btn-sm" data-ex="${i}">Try this example ${svg("chevron")}</button></div></article>`).join("");
    $$("#gallery [data-ex]").forEach((b) => b.addEventListener("click", () => { sound("click"); loadEvent(EXAMPLES[+b.dataset.ex]); }));
  }
  function loadEvent(ev) {
    titleInput.value = ev.title; state.title = ev.title;
    state.types = orderTypes(ev.types.filter((t) => !state.meta || state.meta.types.includes(t)));
    state.otherCat = false;
    titleInput.dispatchEvent(new Event("input"));
    syncTypes();
    $("#stage").hidden = true; $("#studioForm").hidden = false; $("#stepper").style.visibility = ""; $(".progress").style.visibility = "";
    location.hash = "#create";
    setTimeout(() => { goStep(3, false); $("#studio").scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth" }); toast("Example loaded — review the settings, then generate"); }, 80);
  }
  async function drawUnseen() {
    const body = $("#unseenBody");
    body.innerHTML = '<p class="muted">Drawing an event…</p>';
    try {
      const ev = await api("/api/test-event");
      state.unseen = ev;
      body.innerHTML = `<h4>${esc(ev.title)}</h4><div class="ex-labels">${(ev.types.length ? ev.types : ["non précisé"]).map((t) => `<span class="tok">${esc(t)}</span>`).join("")}</div>
        <p class="ref-label">Human-written reference (DATAtourisme)</p><blockquote>${esc(ev.reference)}</blockquote>`;
      $("#tryUnseenBtn").disabled = false;
    } catch (err) { body.innerHTML = `<p class="error">${esc(err.message)}</p>`; }
  }
  $("#drawBtn").addEventListener("click", drawUnseen);
  $("#tryUnseenBtn").addEventListener("click", () => state.unseen && loadEvent(state.unseen));

  // ================================================================== COMPARE
  const cmpInput = $("#cmpTitleInput");
  function renderCompareBar() {
    if (document.activeElement !== cmpInput) cmpInput.value = titleInput.value;
    $("#cmpTypes").innerHTML = (state.types.length ? state.types : []).map((t) =>
      `<button type="button" class="chip on" data-type="${esc(t)}" aria-label="Remove ${esc(t)}">${esc(t)} ${svg("x")}</button>`).join("") ||
      '<span class="chip">type : non précisé</span>';
    $("#cmpSettings").innerHTML = `<span class="pillx">${esc(settingsText())}</span><button type="button" class="pillx" id="cmpEdit">Edit settings</button>`;
    $("#cmpEdit").addEventListener("click", () => { location.hash = "#create"; setTimeout(() => { if (validTitle()) goStep(3); }, 60); });
    const avail = new Set((state.meta?.models || []).map((m) => m.name));
    $$(".duel-card").forEach((c) => { if (!c.dataset.filled) duelCard(c, null, avail.has(c.dataset.model)); });
  }
  $("#cmpTypes").addEventListener("click", (e) => { const c = e.target.closest("button.chip"); if (c) toggleType(c.dataset.type); });
  cmpInput.addEventListener("input", () => { titleInput.value = cmpInput.value; titleInput.dispatchEvent(new Event("input")); $("#cmpErr").textContent = ""; });

  function metricFor(model, method, key) {
    const row = (state.results?.comparison || []).find((r) => r.model === model && r.decoding === method);
    return row && row[key] != null ? row[key] : null;
  }
  function duelCard(card, r, available, method) {
    const kind = card.dataset.model;
    const m = (state.meta?.models || []).find((x) => x.name === kind);
    const label = m?.label || (kind === "attention" ? "LSTM + Bahdanau attention" : "LSTM Encoder–Decoder");
    const arch = m?.architecture || "";
    const mth = method || state.method;
    let body;
    if (!available) body = `<p class="dtext placeholder">This model has not been trained yet (no <code>models/${esc(kind)}/best.pt</code>).</p>`;
    else if (r === "loading") body = `<p class="dtext loading" aria-label="Generating"></p>`;
    else if (r) body = `<p class="dtext">${r.text.trim() ? r.text.trim().split(/\s+/).map((w, i) => `<span class="w" style="animation-delay:${reducedMotion() ? 0 : i * 28}ms">${esc(w)}</span>`).join(" ") : "<em>(empty output)</em>"}</p>`;
    else body = `<p class="dtext placeholder">Run the comparison to see what this network writes.</p>`;
    const bleu = metricFor(kind, mth, "bleu"), rl = metricFor(kind, mth, "rougeL");
    card.innerHTML = `${svg(kind === "attention" ? "spark" : "other", "ghost-ico")}
      <span class="dk">${kind === "attention" ? "With attention" : "Baseline"}</span>
      <h3>${esc(label)}</h3><p class="arch">${esc(arch)}</p>
      ${body}
      <dl class="dstats">
        <div><dt>Generation time</dt><dd${r && r.time_ms != null ? "" : ' class="na"'}>${r && r.time_ms != null ? r.time_ms.toLocaleString("en-US") + " ms" : "Not measured yet"}</dd></div>
        <div><dt>Tokens</dt><dd${r && r.n_tokens != null ? "" : ' class="na"'}>${r && r.n_tokens != null ? r.n_tokens : "—"}</dd></div>
        <div><dt>Val. perplexity</dt><dd${m?.best_val_ppl != null ? "" : ' class="na"'}>${m?.best_val_ppl != null ? fmt.num(m.best_val_ppl, 1) : "Not available"}</dd></div>
        <div><dt>Test BLEU (${esc(mth)})</dt><dd${bleu != null ? "" : ' class="na"'}>${bleu != null ? fmt.num(bleu, 2) : "Not available"}</dd></div>
        <div><dt>Test ROUGE-L</dt><dd${rl != null ? "" : ' class="na"'}>${rl != null ? fmt.num(rl, 2) : "Not available"}</dd></div>
        <div><dt>Parameters</dt><dd${m?.n_params != null ? "" : ' class="na"'}>${m?.n_params != null ? fmt.params(m.n_params) : "Not available"}</dd></div>
      </dl>`;
  }
  $("#cmpForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = cmpInput.value.trim();
    if (title.length < 2) { $("#cmpErr").textContent = "Enter an event title first."; cmpInput.focus(); sound("error"); return; }
    const avail = (state.meta?.models || []).map((m) => m.name).filter((n) => n === "baseline" || n === "attention");
    if (!avail.length) { $("#cmpErr").textContent = "No trained model found."; return; }
    $("#cmpErr").textContent = ""; sound("click");
    const btn = $("#cmpBtn"); btn.disabled = true; btn.textContent = "Generating…";
    $$(".duel-card").forEach((c) => duelCard(c, avail.includes(c.dataset.model) ? "loading" : null, avail.includes(c.dataset.model)));
    try {
      const data = await api("/api/generate", { ...payload(), title, models: avail });
      $$(".duel-card").forEach((c) => {
        const r = data.results.find((x) => x.model === c.dataset.model);
        c.dataset.filled = "1"; duelCard(c, r || null, !!r, data.method);
      });
      sound("success");
    } catch (err) {
      $("#cmpErr").textContent = err.message; sound("error");
      $$(".duel-card").forEach((c) => { delete c.dataset.filled; duelCard(c, null, avail.includes(c.dataset.model)); });
    } finally { btn.disabled = false; btn.textContent = "Run comparison"; }
  });

  // ================================================================== RESULTS
  const COLORS = { attention: "#a78bfa", baseline: "#67e8f9" };
  async function loadResults() {
    try { state.results = await api("/api/results"); } catch { state.results = null; }
    const c = state.results?.cleaning;
    if (c?.pairs) { $("[data-fact='pairs']").textContent = fmt.int(c.pairs); $("#footPairs").textContent = `${fmt.int(c.pairs)} (type + title → description) pairs`; }
  }
  function renderResults() {
    const R = state.results, models = state.meta?.models || [];
    if (!R) { $("#kpis").innerHTML = '<div class="empty" style="grid-column:1/-1">Could not load results from the server.</div>'; return; }
    const c = R.cleaning || {};
    const kp = [
      [fmt.int(c.raw_rows), "raw DATAtourisme rows"], [fmt.int(c.pairs), "clean (input, target) pairs"],
      [c.split ? `${fmt.int(c.split.train)}` : null, `train events${c.split ? ` · ${fmt.int(c.split.val)} val · ${fmt.int(c.split.test)} test` : ""}`],
      [fmt.int(c.src_vocab), "source vocabulary"], [fmt.int(c.tgt_vocab), "target vocabulary"],
    ];
    $("#kpis").innerHTML = kp.map(([v, l]) => `<div class="kpi"><div class="v">${v ?? '<span style="font-size:1rem;color:var(--faint)">Not available</span>'}</div><div class="l">${esc(l)}</div></div>`).join("");

    $("#modelTiles").innerHTML = models.length ? models.map((m) => `<div class="mtile ${esc(m.kind)}">
      <h4><span style="width:10px;height:10px;border-radius:50%;background:${COLORS[m.kind] || "#fff"}"></span>${esc(m.label)}
        ${m.subset ? `<span class="badge warn" title="Trained on a subset">smoke test · ${fmt.int(m.subset)} ex.</span>` : ""}</h4>
      <dl>
        <div><dt>Parameters</dt><dd>${na(fmt.params(m.n_params))}</dd></div>
        <div><dt>Training time</dt><dd>${na(fmt.mins(m.train_time_s))}</dd></div>
        <div><dt>Epochs (best)</dt><dd>${m.epochs_run != null ? `${m.epochs_run} (${m.best_epoch})` : na(null)}</dd></div>
        <div><dt>Best val. loss</dt><dd>${na(fmt.num(m.best_val_loss, 3))}</dd></div>
        <div><dt>Val. perplexity</dt><dd>${na(fmt.num(m.best_val_ppl, 1))}</dd></div>
        <div><dt>Train examples</dt><dd>${na(fmt.int(m.train_size))}</dd></div>
      </dl></div>`).join("") : '<div class="empty" style="grid-column:1/-1">No trained model found in models/.</div>';

    const newest = Math.max(0, ...models.map((m) => m.updated || 0));
    const notice = $("#resNotice");
    if (R.comparison && R.comparison_updated && newest > R.comparison_updated) {
      notice.hidden = false;
      notice.textContent = "A model was retrained after the test metrics were computed. The test-set numbers below describe the previous checkpoints — run scripts/04_evaluate.py to refresh them.";
    } else notice.hidden = true;

    // loss chart model selector
    const hNames = Object.keys(R.history || {});
    if (!state.lossModel || !hNames.includes(state.lossModel)) state.lossModel = hNames.includes("attention") ? "attention" : hNames[0];
    const lm = $("#lossModel");
    lm.innerHTML = hNames.map((n) => `<button type="button" role="radio" data-value="${esc(n)}">${esc(n)}</button>`).join("") + '<span class="seg-thumb"></span>';
    if (hNames.length) segmented(lm, state.lossModel, (v) => { state.lossModel = v; lossChart(); });
    lossChart();
    if (!renderResults.seg) { renderResults.seg = segmented($("#metricDecoding"), state.metricDecoding, (v) => { state.metricDecoding = v; metricChart(); }); }
    requestAnimationFrame(() => $$(".segmented").forEach(placeThumb));
    metricChart();
    metricTable();
  }

  function lossChart() {
    const el = $("#lossChart"), h = state.results?.history?.[state.lossModel];
    if (!h || !h.length) { el.innerHTML = '<div class="empty">Training history not available.</div>'; return; }
    const W = 520, H = 240, P = { l: 40, r: 16, t: 14, b: 30 };
    const ys = h.flatMap((r) => [r.train_loss, r.val_loss]).filter((v) => v != null);
    let y0 = Math.min(...ys), y1 = Math.max(...ys); const pad = (y1 - y0 || 1) * 0.12; y0 -= pad; y1 += pad;
    const e0 = h[0].epoch, e1 = h[h.length - 1].epoch;
    const X = (e) => P.l + (e1 === e0 ? (W - P.l - P.r) / 2 : ((e - e0) / (e1 - e0)) * (W - P.l - P.r));
    const Y = (v) => P.t + (1 - (v - y0) / (y1 - y0)) * (H - P.t - P.b);
    const ticks = [...Array(5)].map((_, i) => y0 + ((y1 - y0) * i) / 4);
    const col = COLORS[state.lossModel.split("_")[0]] || "#c4b5fd";
    const series = [["train_loss", "Training", col, ""], ["val_loss", "Validation", "#f0abfc", "6 5"]];
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Training and validation loss per epoch for ${esc(state.lossModel)}">`;
    ticks.forEach((t) => { s += `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${P.l - 8}" y="${Y(t) + 3}" text-anchor="end">${t.toFixed(2)}</text>`; });
    h.forEach((r) => { s += `<text x="${X(r.epoch)}" y="${H - 10}" text-anchor="middle">${r.epoch}</text>`; });
    series.forEach(([k, , c, dash]) => {
      const pts = h.filter((r) => r[k] != null).map((r) => [X(r.epoch), Y(r[k])]);
      if (!pts.length) return;
      const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
      let len = 0; for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      s += `<path class="line" d="${d}" stroke="${c}" style="--len:${Math.ceil(len) + 2}"/>`;
      pts.forEach((p, i) => { s += `<circle class="pt" cx="${p[0]}" cy="${p[1]}" r="4" fill="${c}" data-k="${k}" data-i="${i}"/>`; });
    });
    s += "</svg>";
    el.innerHTML = s + `<div class="chart-legend"><span><i style="background:${col}"></i>Training loss</span><span><i style="background:#f0abfc"></i>Validation loss</span><span>x: epoch · y: cross-entropy</span></div>`;
    chartHover(el, (c) => { const r = h.filter((x) => x[c.dataset.k] != null)[+c.dataset.i]; return `Epoch ${r.epoch} · ${c.dataset.k === "train_loss" ? "train" : "val"} ${(+r[c.dataset.k]).toFixed(3)}`; });
  }

  function metricChart() {
    const el = $("#metricChart"), rows = state.results?.comparison;
    if (!rows || !rows.length) { el.innerHTML = '<div class="empty">Test metrics not available — run scripts/04_evaluate.py.</div>'; return; }
    const metrics = [["bleu", "BLEU"], ["rouge1", "ROUGE-1"], ["rouge2", "ROUGE-2"], ["rougeL", "ROUGE-L"], ["token_acc", "Token acc. %", 100]];
    const kinds = ["baseline", "attention"].filter((k) => rows.some((r) => r.model === k));
    const val = (k, m) => { const r = rows.find((x) => x.model === k && x.decoding === state.metricDecoding); return r && r[m[0]] != null ? r[m[0]] * (m[2] || 1) : null; };
    const all = metrics.flatMap((m) => kinds.map((k) => val(k, m))).filter((v) => v != null);
    const vmax = Math.max(1, ...all) * 1.15;
    const W = 520, H = 240, P = { l: 30, r: 10, t: 16, b: 30 }, gw = (W - P.l - P.r) / metrics.length, bw = Math.min(26, (gw - 18) / kinds.length);
    const Y = (v) => P.t + (1 - v / vmax) * (H - P.t - P.b);
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Test metrics, baseline versus attention, ${esc(state.metricDecoding)} decoding">`;
    [0, 0.5, 1].forEach((f) => { const v = vmax * f; s += `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${Y(v)}" y2="${Y(v)}"/><text x="${P.l - 6}" y="${Y(v) + 3}" text-anchor="end">${v.toFixed(0)}</text>`; });
    metrics.forEach((m, mi) => {
      const gx = P.l + mi * gw + (gw - bw * kinds.length - 4 * (kinds.length - 1)) / 2;
      kinds.forEach((k, ki) => {
        const v = val(k, m), x = gx + ki * (bw + 4);
        if (v == null) { s += `<text x="${x + bw / 2}" y="${Y(0) - 6}" text-anchor="middle">n/a</text>`; return; }
        const y = Y(v), hgt = Math.max(1.5, Y(0) - y);
        s += `<rect class="bar" x="${x}" y="${Y(0) - hgt}" width="${bw}" height="${hgt}" rx="4" fill="${COLORS[k]}" opacity="${k === "attention" ? 1 : 0.75}" style="animation-delay:${(mi * 80 + ki * 40)}ms" data-tipv="${esc(k)} · ${esc(m[1])}: ${v.toFixed(2)}"/>`;
        s += `<text class="val" x="${x + bw / 2}" y="${Y(0) - hgt - 5}" text-anchor="middle">${v < 10 ? v.toFixed(1) : v.toFixed(0)}</text>`;
      });
      s += `<text x="${P.l + mi * gw + gw / 2}" y="${H - 10}" text-anchor="middle">${esc(m[1])}</text>`;
    });
    s += "</svg>";
    el.innerHTML = s + `<div class="chart-legend">${kinds.map((k) => `<span><i style="background:${COLORS[k]}"></i>${k}</span>`).join("")}<span>Test split · ${esc(state.metricDecoding)} decoding · higher is better</span></div>`;
    chartHover(el, (c) => c.dataset.tipv, "rect.bar");
  }

  function chartHover(el, text, sel = "circle.pt") {
    let t = null;
    $$(sel, el).forEach((c) => {
      c.addEventListener("pointerenter", () => {
        t = document.createElement("div"); t.className = "chart-tip"; t.textContent = text(c); el.appendChild(t);
        const r = c.getBoundingClientRect(), er = el.getBoundingClientRect();
        t.style.left = r.left - er.left + r.width / 2 + "px"; t.style.top = r.top - er.top + "px";
      });
      c.addEventListener("pointerleave", () => { t && t.remove(); t = null; });
    });
  }

  function metricTable() {
    const rows = state.results?.comparison, el = $("#metricTable");
    if (!rows || !rows.length) { el.innerHTML = '<div class="empty">No evaluation yet: run <code>scripts/04_evaluate.py</code>.</div>'; return; }
    const cols = [["model", "Model"], ["decoding", "Decoding"], ["bleu", "BLEU", 1, 2], ["rouge1", "ROUGE-1", 1, 2], ["rouge2", "ROUGE-2", 1, 2], ["rougeL", "ROUGE-L", 1, 2],
      ["token_acc", "Token acc.", 1, 3], ["perplexity", "Perplexity", -1, 1], ["test_loss", "Test loss", -1, 3], ["repetition_rate", "Repetition", -1, 2], ["distinct2", "Distinct-2", 1, 3], ["avg_gen_len", "Avg. length", 0, 1]];
    const best = {};
    cols.forEach(([k, , dir]) => { if (!dir) return; const v = rows.map((r) => r[k]).filter((x) => x != null); if (v.length && Math.max(...v) !== Math.min(...v)) best[k] = dir > 0 ? Math.max(...v) : Math.min(...v); });
    el.innerHTML = `<table class="metrics"><thead><tr>${cols.map((c) => `<th scope="col">${c[1]}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${cols.map(([k, , dir, d]) => {
      const v = r[k];
      if (d == null) return `<td>${esc(v)}</td>`;
      return `<td class="${v != null && best[k] === v && rows.length > 1 ? "best" : ""}">${v == null ? '<span class="na">Not available</span>' : Number(v).toFixed(d)}</td>`;
    }).join("")}</tr>`).join("")}</tbody></table>`;
  }

  // ================================================================== PARTICLES
  const particles = (() => {
    const cv = $("#particles"), ctx = cv.getContext("2d");
    let pts = [], raf = 0, w = 0, h = 0, mouse = { x: -999, y: -999 };
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    function size() {
      w = cv.clientWidth; h = cv.clientHeight; cv.width = w * dpr; cv.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.round(Math.min(90, (w * h) / 22000));
      pts = [...Array(n)].map(() => ({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.18, vy: (Math.random() - 0.5) * 0.18, r: Math.random() * 1.4 + 0.4, a: Math.random() * 0.5 + 0.2 }));
    }
    function frame(still) {
      ctx.clearRect(0, 0, w, h);
      for (const p of pts) {
        if (!still) {
          p.x += p.vx; p.y += p.vy;
          const dx = p.x - mouse.x, dy = p.y - mouse.y, d = Math.hypot(dx, dy);
          if (d < 120) { p.x += (dx / d) * 0.6; p.y += (dy / d) * 0.6; }
          if (p.x < -10) p.x = w + 10; if (p.x > w + 10) p.x = -10; if (p.y < -10) p.y = h + 10; if (p.y > h + 10) p.y = -10;
        }
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fillStyle = `rgba(214,204,255,${p.a})`; ctx.fill();
      }
      for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
        const a = pts[i], b = pts[j], d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 120) { ctx.strokeStyle = `rgba(167,139,250,${0.12 * (1 - d / 120)})`; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
      }
    }
    function loop() { frame(false); raf = requestAnimationFrame(loop); }
    function reset() { cancelAnimationFrame(raf); size(); if (reducedMotion() || document.hidden) frame(true); else loop(); }
    window.addEventListener("resize", () => { clearTimeout(reset._t); reset._t = setTimeout(reset, 150); });
    document.addEventListener("visibilitychange", reset);
    window.addEventListener("pointermove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; }, { passive: true });
    motionQuery.addEventListener?.("change", reset);
    return { reset };
  })();

  // ================================================================== BOOT
  async function boot() {
    renderCategories(); renderGallery(); route(); particles.reset();
    const status = $("#status");
    try {
      state.meta = await api("/api/meta");
      const n = state.meta.models.length;
      status.classList.add(n ? "ok" : "err");
      $(".status-text", status).textContent = n ? `${n} model${n > 1 ? "s" : ""} online` : "No trained model";
      status.title = n ? state.meta.models.map((m) => m.label).join(" · ") : "Train a model with scripts/03_train.py";
    } catch (err) {
      status.classList.add("err"); $(".status-text", status).textContent = "Server offline"; status.title = err.message;
      state.meta = { models: [], types: [] };
      toast(err.message);
    }
    await loadResults();
    // first visit: pre-fill with the first gallery example so the studio is never empty
    const first = EXAMPLES[0];
    titleInput.value = first.title; state.types = orderTypes(first.types);
    titleInput.dispatchEvent(new Event("input"));
    syncTypes(); renderModelCards(); renderPreview(); renderCompareBar();
    if (currentView === "results") renderResults();
    scheduleLive(0);
    // pick up retrained checkpoints without a page reload
    setInterval(async () => {
      try {
        const m = await api("/api/meta");
        const sig = (x) => x.models.map((k) => k.name + k.updated).join("|");
        if (sig(m) !== sig(state.meta)) {
          state.meta = m; liveLast = null; renderModelCards(); await loadResults();
          if (currentView === "results") renderResults();
          toast("A newly trained model is loaded"); scheduleLive(0);
        }
      } catch { /* server temporarily unavailable */ }
    }, 60000);
    requestAnimationFrame(() => { moveIndicator(); $$(".segmented").forEach(placeThumb); });
  }
  boot();
})();
