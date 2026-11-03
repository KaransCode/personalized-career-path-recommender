/* Loaded in <head> so the saved theme applies before first paint (no flash). */
(function () {
  try {
    var v = localStorage.getItem("cp.theme");
    if (v) { v = JSON.parse(v); if (v && v !== "auto") document.documentElement.setAttribute("data-theme", v); }
  } catch (e) { /* ignore */ }
})();
