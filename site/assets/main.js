// agentlens site — small vanilla interactions. No framework.

// Gently drifting LEGO bricks background.
(() => {
  const canvas = document.querySelector(".matrix");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const colors = ["#d8262c", "#f6c700", "#1577d6", "#36a93b", "#fb7a12", "#ffffff"];
  let width = 0;
  let height = 0;
  let bricks = [];
  let rafId = 0;
  let lastFrame = 0;
  const frameMs = 32;

  // Draw one rounded LEGO brick (with studs) of `studs` knobs wide at x,y, rotated.
  const drawBrick = (b) => {
    const unit = b.unit;          // size of one stud cell
    const w = b.studs * unit;
    const h = unit;
    ctx.save();
    ctx.translate(b.x, b.y);
    ctx.rotate(b.rot);
    ctx.globalAlpha = b.alpha;

    // body
    const r = unit * 0.22;
    ctx.fillStyle = b.color;
    roundRect(-w / 2, -h / 2, w, h, r);
    ctx.fill();
    // bottom bevel (darker)
    ctx.fillStyle = "rgba(0,0,0,.20)";
    roundRect(-w / 2, h / 2 - unit * 0.22, w, unit * 0.22, r);
    ctx.fill();

    // studs on top
    for (let i = 0; i < b.studs; i++) {
      const cx = -w / 2 + unit * (i + 0.5);
      const cy = -h / 2 - unit * 0.16;
      ctx.fillStyle = b.color;
      circle(cx, cy, unit * 0.26);
      ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,.35)";
      circle(cx - unit * 0.06, cy - unit * 0.06, unit * 0.14);
      ctx.fill();
    }
    ctx.restore();
  };

  const roundRect = (x, y, w, h, r) => {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  };
  const circle = (x, y, r) => { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.closePath(); };

  const makeBrick = (seeded) => {
    const unit = 16 + Math.random() * 18;
    return {
      unit,
      studs: 1 + Math.floor(Math.random() * 4),
      x: Math.random() * width,
      y: seeded ? Math.random() * height : height + 40,
      color: colors[Math.floor(Math.random() * colors.length)],
      rot: (Math.random() - 0.5) * 0.5,
      vy: 0.15 + Math.random() * 0.35,
      vr: (Math.random() - 0.5) * 0.004,
      alpha: 0.18 + Math.random() * 0.22,
    };
  };

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = Math.min(Math.max(window.innerHeight * .78, 520), 760);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = Math.max(14, Math.round(width / 60));
    bricks = Array.from({ length: count }, () => makeBrick(true));
  };

  const draw = (time = 0) => {
    if (time - lastFrame < frameMs) { rafId = window.requestAnimationFrame(draw); return; }
    lastFrame = time;
    ctx.clearRect(0, 0, width, height);
    bricks.forEach((b, i) => {
      b.y -= b.vy;
      b.rot += b.vr;
      if (b.y < -50) bricks[i] = makeBrick(false);
      drawBrick(b);
    });
    rafId = window.requestAnimationFrame(draw);
  };

  const drawStatic = () => {
    ctx.clearRect(0, 0, width, height);
    bricks.forEach(drawBrick);
  };

  const start = () => {
    window.cancelAnimationFrame(rafId);
    lastFrame = 0;
    resize();
    if (reduceMotion.matches) {
      drawStatic();
    } else {
      draw();
    }
  };

  window.addEventListener("resize", start);
  if (reduceMotion.addEventListener) {
    reduceMotion.addEventListener("change", start);
  } else {
    reduceMotion.addListener(start);
  }
  start();
})();

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
