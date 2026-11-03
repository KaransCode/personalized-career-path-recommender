"use strict";

/* Small dependency-free SVG charts. Colours come from the theme's CSS variables,
   so every chart follows whichever theme is active. */
const Charts = (() => {
  const NS = "http://www.w3.org/2000/svg";

  function s(tag, attrs, ...kids) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      e.setAttribute(k, v === true ? "" : v);
    }
    for (const c of kids.flat(Infinity)) {
      if (c == null || c === false) continue;
      e.append(c instanceof Node ? c : document.createTextNode(String(c)));
    }
    return e;
  }
  const money = (v) => `₹${Number.isInteger(v) ? v : v.toFixed(1)}`;

  /* Radar: items = [{label, value 0..1}] */
  function radar(items) {
    const W = 460, H = 330, cx = W / 2, cy = H / 2, R = 108, n = items.length;
    const pt = (i, v) => { const a = -Math.PI / 2 + (2 * Math.PI * i) / n; return [cx + Math.cos(a) * R * v, cy + Math.sin(a) * R * v]; };
    const poly = (v) => items.map((_, i) => pt(i, v).map((x) => x.toFixed(1)).join(",")).join(" ");
    const svg = s("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img",
      "aria-label": "Radar chart of how close you are to a role in each field: " + items.map((i) => `${i.label} ${Math.round(i.value * 100)}%`).join(", ") });
    [0.25, 0.5, 0.75, 1].forEach((r) => svg.append(s("polygon", { class: "grid", points: poly(r) })));
    items.forEach((_, i) => { const [x, y] = pt(i, 1); svg.append(s("line", { class: "grid", x1: cx, y1: cy, x2: x.toFixed(1), y2: y.toFixed(1) })); });
    svg.append(s("polygon", { points: items.map((it, i) => pt(i, Math.max(it.value, 0.02)).map((x) => x.toFixed(1)).join(",")).join(" "),
      style: "fill:var(--accent);fill-opacity:.2;stroke:var(--accent);stroke-width:2;stroke-linejoin:round" }));
    items.forEach((it, i) => {
      const [x, y] = pt(i, Math.max(it.value, 0.02));
      svg.append(s("circle", { cx: x.toFixed(1), cy: y.toFixed(1), r: 4, style: "fill:var(--accent)" }, s("title", {}, `${it.label}: ${Math.round(it.value * 100)}%`)));
      const [lx, ly] = pt(i, 1.2), cos = Math.cos(-Math.PI / 2 + (2 * Math.PI * i) / n);
      const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
      svg.append(s("text", { x: lx.toFixed(1), y: ly.toFixed(1), "text-anchor": anchor },
        s("tspan", { x: lx.toFixed(1), dy: "-0.1em" }, it.label),
        s("tspan", { x: lx.toFixed(1), dy: "1.25em", style: "fill:var(--ink);font-weight:600" }, `${Math.round(it.value * 100)}%`)));
    });
    return svg;
  }

  /* Pay range per experience band. bands = 4 x ([min,max]|null), labels = band names, years = marker.
     Each band is drawn over the years it covers, so the chart always agrees with the headline numbers. */
  function salaryCurve(bands, labels, years) {
    const W = 640, H = 280, m = { l: 50, r: 16, t: 30, b: 34 };
    const starts = [0, 2, 5, 8], ends = [2, 5, 8, 15];
    const X = (v) => m.l + (v / 15) * (W - m.l - m.r);
    const real = bands.filter(Boolean);
    const svg = s("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Pay range by years of experience" });
    if (!real.length) { svg.append(s("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, "No pay data for this role")); return svg; }
    const top = Math.max(...real.map((b) => b[1])) * 1.1, step = top <= 40 ? 10 : top <= 80 ? 20 : 25;
    const maxY = Math.ceil(top / step) * step;
    const Y = (v) => H - m.b - (v / maxY) * (H - m.t - m.b);
    for (let t = 0; t <= maxY; t += step) {
      svg.append(s("line", { class: "grid", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) }), s("text", { x: m.l - 8, y: Y(t) + 4, "text-anchor": "end" }, `₹${t}L`));
    }
    [0, 2, 5, 8, 15].forEach((t) => svg.append(s("text", { x: X(t), y: H - 12, "text-anchor": t === 0 ? "start" : t === 15 ? "end" : "middle" }, t === 15 ? "15 yrs" : t)));
    const active = years < 2 ? 0 : years < 5 ? 1 : years < 8 ? 2 : 3;
    bands.forEach((b, i) => {
      const x0 = X(starts[i]) + 2, w = X(ends[i]) - X(starts[i]) - 4, on = i === active;
      if (!b) {
        svg.append(s("text", { x: x0 + w / 2, y: H - m.b - 8, "text-anchor": "middle" }, "Not typical"));
        return;
      }
      svg.append(s("rect", { x: x0, y: Y(b[1]), width: w, height: Y(b[0]) - Y(b[1]), rx: 6,
        style: `fill:var(--accent);fill-opacity:${on ? 0.4 : 0.14};stroke:var(--accent);stroke-opacity:${on ? 1 : 0.5};stroke-width:${on ? 2 : 1}` },
        s("title", {}, `${labels[i]}: ${money(b[0])}–${b[1]} LPA`)));
      svg.append(s("text", { x: x0 + w / 2, y: Y(b[1]) - 7, "text-anchor": "middle", style: on ? "fill:var(--ink);font-weight:600" : "" }, `${money(b[0])}–${b[1]}L`));
    });
    const mx = X(Math.min(Math.max(years, 0), 15));
    svg.append(s("line", { x1: mx, x2: mx, y1: m.t - 6, y2: H - m.b, style: "stroke:var(--ink);stroke-opacity:.5;stroke-dasharray:4 4" }),
      s("circle", { cx: mx, cy: H - m.b, r: 5, style: "fill:var(--ink)" }),
      s("text", { x: mx + (mx > W - 120 ? -8 : 8), y: m.t - 12, "text-anchor": mx > W - 120 ? "end" : "start", style: "fill:var(--ink);font-weight:600" }, years === 0 ? "You: fresher" : `You: ${years} yrs`));
    return svg;
  }

  /* Scatter with hover tooltips. points = [{x, y, label, color, href, r}] */
  function scatter(points, { xLabel = "", yLabel = "", xFmt = (v) => v, yFmt = (v) => v, yMin = 0, yDomain = null, yTicks = null, xDomain = null, xTicks = null } = {}) {
    const W = 640, H = 380, m = { l: 70, r: 22, t: 18, b: 48 };
    const svg = s("svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `${yLabel} against ${xLabel}` });
    if (!points.length) { svg.append(s("text", { x: W / 2, y: H / 2, "text-anchor": "middle" }, "Nothing to plot")); return svg; }
    const xv = points.map((p) => p.x), yv = points.map((p) => p.y);
    const x0 = xDomain ? xDomain[0] : Math.floor(Math.min(...xv) - 0.5), x1 = xDomain ? xDomain[1] : Math.ceil(Math.max(...xv) + 0.5);
    const y0 = yDomain ? yDomain[0] : yMin, y1 = yDomain ? yDomain[1] : Math.ceil(Math.max(...yv) * 1.1);
    const X = (v) => m.l + ((v - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
    const Y = (v) => H - m.b - ((v - y0) / (y1 - y0 || 1)) * (H - m.t - m.b);
    (xTicks || [0, 1, 2, 3, 4].map((i) => Math.round(x0 + ((x1 - x0) * i) / 4))).forEach((xt) =>
      svg.append(s("text", { x: X(xt), y: H - m.b + 18, "text-anchor": "middle" }, xFmt(xt))));
    const yt = yTicks || [0, 1, 2, 3, 4].map((i) => Math.round(y0 + ((y1 - y0) * i) / 4));
    yt.forEach((t) => svg.append(s("line", { class: "grid", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) }), s("text", { x: m.l - 8, y: Y(t) + 4, "text-anchor": "end" }, yFmt(t))));
    svg.append(s("text", { x: (m.l + W - m.r) / 2, y: H - 6, "text-anchor": "middle" }, xLabel), s("text", { x: 14, y: (m.t + H - m.b) / 2, transform: `rotate(-90 14 ${(m.t + H - m.b) / 2})`, "text-anchor": "middle" }, yLabel));
    const tip = s("g", { class: "tip", style: "display:none;pointer-events:none" }, s("rect", { rx: 6, height: 22 }), s("text", { y: 15 }));
    const show = (p) => {
      const t = tip.querySelector("text"); t.textContent = p.label; const w = p.label.length * 6.3 + 16;
      let tx = X(p.x) - w / 2; tx = Math.max(4, Math.min(tx, W - w - 4));
      tip.querySelector("rect").setAttribute("width", w); tip.querySelector("rect").setAttribute("x", tx); t.setAttribute("x", tx + 8);
      const ty = Y(p.y) - (p.r || 8) - 30; tip.setAttribute("transform", `translate(0 ${Math.max(2, ty)})`); tip.style.display = "";
    };
    // draw large bubbles first so small ones stay clickable
    [...points].sort((a, b) => (b.r || 8) - (a.r || 8)).forEach((p) => {
      const dot = s("circle", { class: "dot", cx: X(p.x).toFixed(1), cy: Y(p.y).toFixed(1), r: p.r || 8, style: `fill:${p.color || "var(--accent)"};fill-opacity:.85` });
      const node = p.href ? s("a", { href: p.href, "aria-label": p.label }, dot) : dot;
      node.addEventListener("mouseenter", () => show(p)); node.addEventListener("focus", () => show(p));
      node.addEventListener("mouseleave", () => { tip.style.display = "none"; }); node.addEventListener("blur", () => { tip.style.display = "none"; });
      svg.append(node);
    });
    svg.append(tip);
    return svg;
  }

  /* Donut: parts = [{value, color}], centre = [big, small] */
  function donut(parts, centre = []) {
    const S = 132, r = 52, C = 2 * Math.PI * r, total = parts.reduce((a, p) => a + p.value, 0) || 1;
    const svg = s("svg", { class: "chart", viewBox: `0 0 ${S} ${S}`, style: "width:132px;height:132px", role: "img", "aria-label": centre.join(", ") });
    svg.append(s("circle", { cx: S / 2, cy: S / 2, r, style: "fill:none;stroke:var(--track);stroke-width:16" }));
    let acc = 0;
    parts.forEach((p) => {
      const len = (p.value / total) * C;
      if (len > 0) svg.append(s("circle", { cx: S / 2, cy: S / 2, r, transform: `rotate(-90 ${S / 2} ${S / 2})`,
        style: `fill:none;stroke:${p.color};stroke-width:16;stroke-opacity:${p.opacity || 1};stroke-dasharray:${len.toFixed(2)} ${(C - len).toFixed(2)};stroke-dashoffset:${(-acc).toFixed(2)}` }));
      acc += len;
    });
    svg.append(s("text", { x: S / 2, y: S / 2 + 2, "text-anchor": "middle", style: "fill:var(--ink);font-size:20px;font-weight:600" }, centre[0] || ""),
      s("text", { x: S / 2, y: S / 2 + 18, "text-anchor": "middle" }, centre[1] || ""));
    return svg;
  }

  return { radar, salaryCurve, scatter, donut };
})();
