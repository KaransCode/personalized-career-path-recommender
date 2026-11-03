"use strict";

/* Shared helpers for every page: navigation, themes, command palette, API calls,
   saved state, salary maths, trends and learning roadmaps. */
const CP = (() => {
  // Same origin when served by Flask (port 5000); otherwise point at Flask.
  const API_BASE = location.port === "5000" ? "" : "http://localhost:5000";
  const CATEGORIES = ["Data", "AI / ML", "Software", "Mobile", "Cloud & Ops", "Security", "Product & Design", "Management"];
  const catColor = (c) => { const i = CATEGORIES.indexOf(c); return `var(--c${i < 0 ? 8 : i + 1})`; };

  /* ---------- tiny DOM helper ---------- */
  function h(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k.startsWith("on") && typeof v === "function") e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? "" : v);
    }
    for (const c of kids.flat(Infinity)) {
      if (c == null || c === false) continue;
      e.append(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return e;
  }

  /* ---------- saved state (browser localStorage) ---------- */
  const store = {
    get(k, d) { try { const v = localStorage.getItem("cp." + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem("cp." + k, JSON.stringify(v)); } catch { /* ignore */ } },
    del(k) { try { localStorage.removeItem("cp." + k); } catch { /* ignore */ } },
  };
  const getProfile = () => store.get("profile", null);
  function setProfile(p) { store.set("profile", p); ["extra", "learn", "years", "target"].forEach((k) => store.del(k)); }
  function clearProfile() { ["profile", "extra", "learn", "years", "target"].forEach((k) => store.del(k)); }
  const getExtra = () => store.get("extra", []);
  const setExtra = (a) => store.set("extra", a);
  const getLearn = () => store.get("learn", []);
  const setLearn = (a) => store.set("learn", a);
  const getTarget = () => store.get("target", null);
  const setTarget = (n) => (n ? store.set("target", n) : store.del("target"));
  const setYears = (v) => store.set("years", v);
  function getYears() {
    const v = store.get("years", null);
    if (typeof v === "number") return v;
    const p = getProfile();
    if (p && typeof p.years_experience === "number") return Math.min(15, Math.round(p.years_experience * 2) / 2);
    return 1;
  }

  /* ---------- API ---------- */
  async function api(path, opts = {}, timeout = 60000) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeout);
    try {
      const resp = await fetch(API_BASE + path, { ...opts, signal: ctrl.signal });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        const e = new Error(data.error || `Request failed (${resp.status}).`);
        e.status = resp.status;
        throw e;
      }
      return data;
    } catch (err) {
      if (err.status) throw err;
      if (err.name === "AbortError") throw new Error("The server took too long to respond. Check the Flask and Neo4j terminals for errors.");
      if (err instanceof TypeError) throw new Error("Can’t reach the API at localhost:5000. Make sure python api/app.py is running.");
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
  const memo = {};
  const cached = (key, path) => (memo[key] ||= api(path).catch((e) => { delete memo[key]; throw e; }));
  const getRoles = () => cached("roles", "/roles");
  const getTrends = () => cached("trends", "/trends");
  const getGuide = () => cached("guide", "/skills-guide");

  /* ---------- skills, coverage, roadmap ---------- */
  function skillSets() {
    const p = getProfile();
    const base = new Set(((p && p.skills) || []).map((s) => s.toLowerCase()));
    getExtra().forEach((s) => base.add(s));
    return { base, learn: new Set(getLearn()) };
  }
  function coverage(required, sets) {
    let have = 0, plan = 0;
    const missing = [];
    for (const s of required) {
      if (sets.base.has(s)) have++;
      else { if (sets.learn.has(s)) plan++; missing.push({ skill: s, planned: sets.learn.has(s) }); }
    }
    return { have, plan, total: required.length, missing };
  }
  function toggleLearn(skill) {
    const l = new Set(getLearn());
    l.has(skill) ? l.delete(skill) : l.add(skill);
    setLearn([...l]);
  }
  function markLearned(skill) {
    if (!getExtra().includes(skill)) setExtra([...getExtra(), skill]);
    setLearn(getLearn().filter((s) => s !== skill));
  }
  /* Order missing skills so prerequisites come first; shorter items first among equals. */
  function buildRoadmap(role, sets, guide) {
    const g = (guide && guide.skills) || {};
    const wk = (s) => (g[s] && g[s].weeks) || 2;
    const missing = role.required_skills.filter((s) => !sets.base.has(s));
    const inSet = new Set(missing), done = new Set(), order = [];
    while (order.length < missing.length) {
      const ready = missing.filter((s) => !done.has(s) && ((g[s] && g[s].after) || []).every((p) => !inSet.has(p) || done.has(p)));
      const pool = ready.length ? ready : missing.filter((s) => !done.has(s));   // cycle guard
      pool.sort((a, b) => wk(a) - wk(b) || a.localeCompare(b));
      order.push(pool[0]); done.add(pool[0]);
    }
    return order.map((s) => ({ skill: s, weeks: wk(s), after: ((g[s] && g[s].after) || []), planned: sets.learn.has(s) }));
  }

  /* ---------- salary ---------- */
  const BAND_STARTS = [1, 3.5, 6.5, 10];            // slider position a band click moves to
  const bandIndex = (y) => (y < 2 ? 0 : y < 5 ? 1 : y < 8 ? 2 : 3);
  const fmtNum = (n) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  const fmtYears = (y) => (y === 0 ? "Fresher" : `${fmtNum(y)} ${y === 1 ? "year" : "years"}`);
  function fmtRange(band, unit = "year") {
    if (!band) return "Usually needs more experience";
    if (unit === "month") { const k = (v) => Math.round((v * 100) / 12); return `₹${k(band[0])}k–${k(band[1])}k / month`; }
    return `₹${fmtNum(band[0])}–${fmtNum(band[1])} LPA`;
  }
  const payAt = (role, years) => role.salary_lpa[bandIndex(years)];
  const roleUrl = (name) => `role.html?name=${encodeURIComponent(name)}`;

  /* ---------- trends ---------- */
  const MOMENTUM = { surging: "Surging", rising: "Rising", steady: "Steady", selective: "Selective" };
  const trendTag = (t) => (t ? h("span", { class: "tag trend " + t.momentum, title: t.note }, MOMENTUM[t.momentum] || t.momentum) : null);
  const skillTrend = (trends, skill) => ((trends && trends.skills) || []).find((s) => s.skill === skill) || null;
  const isHotSkill = (trends, skill) => { const t = skillTrend(trends, skill); return !!t && (t.momentum === "surging" || t.momentum === "rising"); };
  const pips = (n) => h("span", { class: "pips", role: "img", "aria-label": `Outlook ${n} out of 5` }, [1, 2, 3, 4, 5].map((i) => h("i", { class: i <= n ? "on" : "" })));

  /* ---------- themes ---------- */
  const THEMES = [["auto", "Auto", ["#fbfbfc", "#2457d6"]], ["light", "Light", ["#fbfbfc", "#2457d6"]], ["dark", "Dark", ["#0f1218", "#6c93f5"]],
                  ["midnight", "Midnight", ["#0a0f1f", "#7aa2ff"]], ["forest", "Forest", ["#0d1813", "#5fd49a"]], ["sunset", "Sunset", ["#fff7ef", "#d9480f"]]];
  function applyTheme(t) {
    t === "auto" ? document.documentElement.removeAttribute("data-theme") : document.documentElement.setAttribute("data-theme", t);
    store.set("theme", t);
  }
  function themeButton() {
    const current = () => store.get("theme", "auto");
    const btn = h("button", { class: "iconbtn", type: "button", "aria-haspopup": "true", "aria-expanded": "false" }, "Theme");
    let menu = null;
    const close = () => { if (menu) { menu.remove(); menu = null; btn.setAttribute("aria-expanded", "false"); } };
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menu) return close();
      menu = h("div", { class: "menu", role: "menu" }, THEMES.map(([id, label, [bg, ac]]) =>
        h("button", { type: "button", role: "menuitemradio", "aria-checked": String(current() === id),
          onclick: () => { applyTheme(id); close(); } },
          h("span", { class: "swatch", style: `background:${bg}` }, h("i", { style: `background:${ac}` })), label)));
      btn.parentElement.append(menu);
      btn.setAttribute("aria-expanded", "true");
    });
    document.addEventListener("click", (e) => { if (menu && !menu.contains(e.target)) close(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    return btn;
  }

  /* ---------- command palette (Ctrl/Cmd+K or /) ---------- */
  let paletteDlg = null;
  async function openPalette() {
    if (!paletteDlg) {
      const input = h("input", { type: "text", placeholder: "Jump to a role, skill or page", "aria-label": "Search", autocomplete: "off" });
      const list = h("ul", { role: "listbox" });
      paletteDlg = h("dialog", { id: "palette", "aria-label": "Search" }, input, list, h("div", { class: "hint" }, "Arrow keys to move, Enter to open, Esc to close"));
      document.body.append(paletteDlg);
      let items = [], sel = 0, roles = [];
      const pages = [["Home", "index.html"], ["Results", "results.html"], ["Explore roles", "explore.html"], ["Market trends", "trends.html"]];
      const render = () => {
        const q = input.value.trim().toLowerCase();
        items = [
          ...pages.filter(([n]) => !q || n.toLowerCase().includes(q)).map(([n, u]) => ({ label: n, hint: "Page", href: u })),
          ...roles.filter((r) => !q || r.name.toLowerCase().includes(q) || r.required_skills.some((s) => s.includes(q)))
                  .slice(0, 8).map((r) => ({ label: r.name, hint: r.category, href: roleUrl(r.name) })),
        ].slice(0, 10);
        sel = Math.min(sel, Math.max(items.length - 1, 0));
        list.replaceChildren(...items.map((it, i) => h("li", {}, h("a", { href: it.href, role: "option", "aria-selected": String(i === sel) },
          h("span", {}, it.label), h("span", { class: "muted small" }, it.hint)))));
        if (!items.length) list.replaceChildren(h("li", { class: "muted", style: "padding:12px" }, "Nothing found"));
      };
      input.addEventListener("input", () => { sel = 0; render(); });
      input.addEventListener("keydown", (e) => {
        if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(sel + 1, items.length - 1); render(); }
        else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(sel - 1, 0); render(); }
        else if (e.key === "Enter" && items[sel]) { e.preventDefault(); location.href = items[sel].href; }
      });
      paletteDlg.addEventListener("click", (e) => { if (e.target === paletteDlg) paletteDlg.close(); });
      paletteDlg._render = render;
      getRoles().then((d) => { roles = d.roles; render(); }).catch(() => {});
      render();
    }
    paletteDlg.showModal();
    paletteDlg.querySelector("input").value = "";
    paletteDlg._render();
    paletteDlg.querySelector("input").focus();
  }

  /* ---------- nav, toast, small components ---------- */
  function renderNav() {
    let page = location.pathname.split("/").pop();
    if (!page) page = "index.html";
    const current = page === "role.html" ? "explore.html" : page;
    const link = (href, label) => h("a", { class: "link", href, "aria-current": current === href ? "page" : null }, label);
    const search = h("button", { class: "iconbtn", type: "button", onclick: openPalette, "aria-label": "Search roles and pages" }, "Search", h("kbd", {}, "Ctrl K"));
    const nav = h("nav", { class: "nav", "aria-label": "Main" },
      h("div", { class: "nav-in" },
        h("a", { class: "brand", href: "index.html" }, "Career Paths"),
        link("index.html", "Home"), link("results.html", "Results"), link("explore.html", "Explore"), link("trends.html", "Trends"),
        h("div", { class: "nav-tools" }, search, themeButton())));
    document.body.prepend(nav);
    document.addEventListener("keydown", (e) => {
      const typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target && e.target.tagName) || "");
      if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") || (e.key === "/" && !typing)) { e.preventDefault(); openPalette(); }
    });
  }

  function toast(msg) {
    let box = document.getElementById("toasts");
    if (!box) { box = h("div", { id: "toasts", "aria-live": "polite" }); document.body.append(box); }
    const t = h("div", { class: "toast" }, msg);
    box.append(t);
    setTimeout(() => t.classList.add("out"), 2600);
    setTimeout(() => t.remove(), 3000);
  }

  function rail(cov) {
    const r = h("div", { class: "rail", role: "img", "aria-label": `${cov.have} matched, ${cov.plan} planned, of ${cov.total} required skills` });
    for (let i = 0; i < cov.total; i++) r.append(h("span", { class: i < cov.have ? "on" : i < cov.have + cov.plan ? "plan" : "" }));
    return r;
  }

  /* Experience slider shared by several pages. onChange(years) fires on input. */
  function expControl(onChange) {
    const out = h("output", { "aria-live": "polite" });
    const input = h("input", { type: "range", min: 0, max: 15, step: 0.5, value: getYears(), "aria-label": "Years of experience" });
    const sync = () => { out.textContent = fmtYears(+input.value); input.style.setProperty("--pct", (input.value / 15) * 100 + "%"); };
    input.addEventListener("input", () => { setYears(+input.value); sync(); onChange(+input.value); });
    sync();
    const wrap = h("label", { class: "exp" }, h("span", { class: "exp-label" }, "Your experience"), input, out);
    wrap.setYears = (y) => { input.value = y; setYears(y); sync(); };
    return wrap;
  }

  function skeletons(n, height = 96) {
    return h("div", { style: "display:grid;gap:12px" }, Array.from({ length: n }, () => h("div", { class: "skeleton", style: `height:${height}px` })));
  }

  /* Horizontal bar list. items: {label, value, max, text, href?, color?, planned?, onclick?, extra?} */
  function hbars(items) {
    return h("div", { class: "hb" }, items.map((it) => {
      const lbl = it.href ? h("a", { class: "lbl", href: it.href }, it.label, it.extra) : h("span", { class: "lbl" }, it.label, it.extra);
      const row = [lbl, h("span", { class: "trk" }, h("span", { class: "fl", style: `width:${Math.max(2, (it.value / it.max) * 100)}%;${it.color ? `background:${it.color}` : ""}` })), h("span", { class: "val" }, it.text)];
      return it.onclick
        ? h("button", { type: "button", class: "hb-row" + (it.planned ? " planned" : ""), title: it.title || "", onclick: it.onclick }, row)
        : h("div", { class: "hb-row" }, row);
    }));
  }

  return { h, api, store, CATEGORIES, catColor, getRoles, getTrends, getGuide, getProfile, setProfile, clearProfile, getExtra, setExtra, getLearn, setLearn,
           getTarget, setTarget, getYears, setYears, skillSets, coverage, toggleLearn, markLearned, buildRoadmap, BAND_STARTS, bandIndex, fmtNum, fmtYears,
           fmtRange, payAt, roleUrl, trendTag, skillTrend, isHotSkill, pips, renderNav, toast, rail, expControl, skeletons, hbars, openPalette };
})();
