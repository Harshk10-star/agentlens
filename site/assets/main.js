// agentlens site — small vanilla interactions. No framework.

// Syntax highlighting (highlight.js, loaded from CDN in the <head>).
document.addEventListener("DOMContentLoaded", () => {
  if (window.hljs) {
    document.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));
  }
});

// Copy-to-clipboard for any [data-copy] button (copies its target's text).
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-copy]");
  if (!btn) return;
  const sel = btn.getAttribute("data-copy");
  const src = sel ? document.querySelector(sel) : btn.previousElementSibling;
  const text = (src ? src.innerText : btn.dataset.text || "").trim();
  navigator.clipboard.writeText(text).then(() => {
    const old = btn.textContent;
    btn.textContent = "copied";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = old; btn.classList.remove("copied"); }, 1300);
  });
});

// Tabbed code showcase.
document.querySelectorAll("[data-tabs]").forEach((group) => {
  const tabs = group.querySelectorAll(".tab");
  const panels = group.querySelectorAll(".panel");
  tabs.forEach((tab) => tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    panels.forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    const panel = group.querySelector(`#${tab.dataset.panel}`);
    if (panel) panel.classList.add("active");
  }));
});

// Mobile nav toggle.
const navToggle = document.querySelector(".nav-toggle");
if (navToggle) navToggle.addEventListener("click", () =>
  document.querySelector(".nav-links").classList.toggle("open"));

// Docs: mobile sidebar toggle.
const docsToggle = document.querySelector(".docs-toggle");
if (docsToggle) docsToggle.addEventListener("click", () =>
  document.querySelector(".sidebar").classList.toggle("open"));

// Docs: scrollspy — highlight the sidebar link for the section in view.
const sideLinks = [...document.querySelectorAll(".sidebar a[href^='#']")];
if (sideLinks.length) {
  const byId = new Map(sideLinks.map((a) => [a.getAttribute("href").slice(1), a]));
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) {
        sideLinks.forEach((a) => a.classList.remove("active"));
        const link = byId.get(en.target.id);
        if (link) link.classList.add("active");
      }
    });
  }, { rootMargin: "-80px 0px -70% 0px", threshold: 0 });
  document.querySelectorAll(".content h2[id]").forEach((h) => obs.observe(h));
}
