"""Render a Trace (plus any loop warnings) to a self-contained HTML file.

Stdlib only. The output is a single .html with inline CSS — open it in any
browser, no server needed.
"""

from __future__ import annotations

import html
import json
import webbrowser
from pathlib import Path
from typing import Any, Optional

from .trace import Trace
from .detectors import LoopWarning, detect_loops


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _pretty(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    return str(value)


def _render_warnings(warnings: list[LoopWarning]) -> str:
    if not warnings:
        return '<div class="ok">No loops or repeated tool calls detected.</div>'
    rows = []
    for w in warnings:
        rows.append(
            f'<div class="warn {_esc(w.severity)}">'
            f'<span class="badge">{_esc(w.severity.upper())}</span>'
            f"{_esc(w.message)}</div>"
        )
    return "\n".join(rows)


def _render_step(step, loop_steps: set[int]) -> str:
    looped = " looped" if step.index in loop_steps else ""
    errored = " errored" if step.error else ""
    tool_block = ""
    if step.tool:
        tool_block = f"""
        <div class="toolcall">
          <div class="tool">🔧 {_esc(step.tool)}</div>
          <div class="kv"><b>args</b><pre>{_esc(_pretty(step.args))}</pre></div>
          <div class="kv"><b>result</b><pre>{_esc(_pretty(step.result))}</pre></div>
        </div>"""
    error_block = (
        f'<div class="err">❌ {_esc(step.error)}</div>' if step.error else ""
    )
    thought_block = (
        f'<div class="thought">💭 {_esc(step.thought)}</div>' if step.thought else ""
    )
    return f"""
    <div class="step{looped}{errored}">
      <div class="step-head">
        <span class="num">Step {step.index}</span>
        <span class="meta">{step.tokens} tok · {step.latency_ms:.0f} ms</span>
      </div>
      {thought_block}
      {tool_block}
      {error_block}
    </div>"""


_CSS = """
:root { --bg:#0f1117; --card:#1a1d27; --line:#2a2e3a; --txt:#e6e8ee;
        --muted:#8b90a0; --accent:#6ea8fe; --warn:#f0b429; --err:#ff5c6c; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--txt);
       font:14px/1.5 ui-sans-serif,system-ui,Segoe UI,Roboto,sans-serif; }
.wrap { max-width: 860px; margin: 0 auto; padding: 32px 20px 80px; }
h1 { font-size: 22px; margin: 0 0 4px; }
.sub { color: var(--muted); margin-bottom: 24px; }
.stats { display:flex; gap:12px; margin-bottom: 24px; flex-wrap: wrap; }
.stat { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:12px 16px; min-width:120px; }
.stat .n { font-size:22px; font-weight:600; }
.stat .l { color:var(--muted); font-size:12px; }
.section { font-size:13px; text-transform:uppercase; letter-spacing:.06em;
           color:var(--muted); margin:28px 0 12px; }
.ok { color:#5fd08a; background:var(--card); border:1px solid var(--line);
      border-radius:10px; padding:12px 16px; }
.warn { background:var(--card); border-left:4px solid var(--warn);
        border-radius:8px; padding:10px 14px; margin-bottom:8px; }
.warn.error { border-left-color: var(--err); }
.badge { font-size:11px; font-weight:700; margin-right:8px; color:var(--bg);
         background:var(--warn); padding:1px 6px; border-radius:4px; }
.warn.error .badge { background:var(--err); }
.step { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:14px 16px; margin-bottom:10px; }
.step.looped { border-color: var(--warn); }
.step.errored { border-color: var(--err); }
.step-head { display:flex; justify-content:space-between; align-items:center; }
.num { font-weight:600; }
.meta { color:var(--muted); font-size:12px; }
.thought { color:var(--muted); margin:8px 0; }
.toolcall { margin-top:8px; }
.tool { color:var(--accent); font-weight:600; margin-bottom:6px; }
.kv { margin:4px 0; } .kv b { color:var(--muted); font-size:12px; }
pre { background:#11141c; border:1px solid var(--line); border-radius:6px;
      padding:8px 10px; margin:4px 0 0; overflow:auto; white-space:pre-wrap; }
.err { color:var(--err); margin-top:8px; }
"""


def render_html(trace: Trace, warnings: Optional[list[LoopWarning]] = None) -> str:
    """Return the full HTML document as a string."""
    if warnings is None:
        warnings = detect_loops(trace)
    loop_steps = {i for w in warnings for i in w.step_indexes}

    steps_html = "\n".join(_render_step(s, loop_steps) for s in trace.steps)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentlens — {_esc(trace.name)}</title>
<style>{_CSS}</style></head>
<body><div class="wrap">
  <h1>🔎 {_esc(trace.name)}</h1>
  <div class="sub">agentlens trace report</div>

  <div class="stats">
    <div class="stat"><div class="n">{trace.total_steps}</div><div class="l">steps</div></div>
    <div class="stat"><div class="n">{trace.total_tokens}</div><div class="l">tokens</div></div>
    <div class="stat"><div class="n">{trace.total_latency_ms:.0f}</div><div class="l">ms total</div></div>
    <div class="stat"><div class="n">{len(trace.errors)}</div><div class="l">errors</div></div>
  </div>

  <div class="section">Loop detection</div>
  {_render_warnings(warnings)}

  <div class="section">Timeline</div>
  {steps_html}
</div></body></html>"""


def generate_html(
    trace: Trace,
    output_path: str | Path = "report.html",
    *,
    warnings: Optional[list[LoopWarning]] = None,
    open_browser: bool = False,
) -> Path:
    """Write the report to disk and return its path.

    Set open_browser=True to pop it open automatically.
    """
    path = Path(output_path)
    path.write_text(render_html(trace, warnings), encoding="utf-8")
    if open_browser:
        webbrowser.open(path.resolve().as_uri())
    return path


# --- eval report (multiple cases with pass/fail) -------------------------
def _render_metric(result) -> str:
    cls = "mpass" if result.passed else "mfail"
    icon = "✓" if result.passed else "✗"
    detail = f' <span class="mdetail">— {_esc(result.detail)}</span>' if result.detail else ""
    return f'<div class="metric {cls}">{icon} {_esc(result.metric)}{detail}</div>'


def _render_case(case_result, index: int) -> str:
    passed = case_result.passed
    badge = "PASS" if passed else "FAIL"
    cls = "pass" if passed else "fail"
    metrics_html = "\n".join(_render_metric(r) for r in case_result.results)
    if case_result.error:
        metrics_html += f'<div class="metric mfail">✗ agent error: {_esc(case_result.error)}</div>'

    steps_html = ""
    if case_result.trace is not None:
        loop_steps = {i for w in detect_loops(case_result.trace) for i in w.step_indexes}
        steps_html = "".join(_render_step(s, loop_steps) for s in case_result.trace.steps)

    label = _esc(case_result.case.label(index))
    return f"""
    <div class="case {cls}">
      <div class="case-head">
        <span class="case-badge {cls}">{badge}</span>
        <span class="case-name">{label}</span>
      </div>
      <div class="case-input">input: {_esc(case_result.case.input)}</div>
      <div class="metrics">{metrics_html}</div>
      <details class="trace-toggle"><summary>trace ({case_result.trace.total_steps if case_result.trace else 0} steps)</summary>
        {steps_html}
      </details>
    </div>"""


_EVAL_CSS = """
.case { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:14px 16px; margin-bottom:12px; border-left:4px solid var(--line); }
.case.pass { border-left-color:#5fd08a; }
.case.fail { border-left-color: var(--err); }
.case-head { display:flex; align-items:center; gap:10px; }
.case-badge { font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px; color:var(--bg); }
.case-badge.pass { background:#5fd08a; } .case-badge.fail { background:var(--err); }
.case-name { font-weight:600; }
.case-input { color:var(--muted); font-size:13px; margin:6px 0 10px; }
.metric { font-size:13px; margin:3px 0; } .metric.mpass { color:#5fd08a; } .metric.mfail { color:var(--err); }
.mdetail { color:var(--muted); }
.trace-toggle { margin-top:10px; } .trace-toggle summary { cursor:pointer; color:var(--accent); font-size:13px; }
.bigstat { font-size:34px; font-weight:700; }
"""


def render_eval_html(report) -> str:
    """Return the full HTML document for an eval Report."""
    cases_html = "\n".join(_render_case(cr, i) for i, cr in enumerate(report.case_results))
    rate = report.pass_rate
    rate_color = "#5fd08a" if rate == 1.0 else ("var(--warn)" if rate >= 0.5 else "var(--err)")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentlens eval — {_esc(report.name)}</title>
<style>{_CSS}{_EVAL_CSS}</style></head>
<body><div class="wrap">
  <h1>🧪 {_esc(report.name)}</h1>
  <div class="sub">agentlens eval report</div>
  <div class="stats">
    <div class="stat"><div class="bigstat" style="color:{rate_color}">{rate:.0%}</div><div class="l">pass rate</div></div>
    <div class="stat"><div class="n">{report.passed}/{report.total}</div><div class="l">cases passed</div></div>
  </div>
  <div class="section">Cases</div>
  {cases_html}
</div></body></html>"""


def generate_eval_html(
    report,
    output_path: str | Path = "eval_report.html",
    *,
    open_browser: bool = False,
) -> Path:
    """Write an eval Report to disk and return its path."""
    path = Path(output_path)
    path.write_text(render_eval_html(report), encoding="utf-8")
    if open_browser:
        webbrowser.open(path.resolve().as_uri())
    return path
