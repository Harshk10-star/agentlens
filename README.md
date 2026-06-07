# 🔎 agentlens

Local-first **observability + eval** for AI agents.

Capture every step your agent takes — thoughts, tool calls, tokens, latency,
errors — automatically detect when it gets **stuck in a loop**, and render the
whole run to a self-contained **HTML report**. No backend, no account, no cloud.
The core is **stdlib-only**.

> Working name. Easy to rename.

## Why

Most agent tools either (a) only score the final answer, missing mistakes that
happen mid-run, or (b) require a hosted dashboard (Postgres + ClickHouse, an
account, a cloud). `agentlens` is the opposite: **one trace object, many
lenses**, running entirely on your laptop.

## Install (dev)

```bash
pip install -e .
```

## Quick start

```python
from agentlens import Tracer, detect_loops
from agentlens.report import generate_html

tracer = Tracer("my-agent")

with tracer.step("user wants the weather") as step:
    step.tool_call("get_weather", {"city": "NYC"},
                   result="72F", tokens=120, latency_ms=800)

warnings = detect_loops(tracer.trace)
generate_html(tracer.trace, "report.html", warnings=warnings, open_browser=True)
```

Or just run the demo:

```bash
python example.py   # writes report.html
```

## What's in the box (v0.1)

- **Tracing** — `Tracer` / `Step` / `Trace`; latency timed automatically.
- **Loop detection** — consecutive and frequent repeated tool calls.
- **HTML report** — timeline, per-step tool calls, totals, loop warnings.

## Roadmap

The whole design is layers over the same `Trace`:

- **Eval layer** — assertion metrics (`Contains`, `Regex`, `ToolWasCalled`),
  opt-in `LLMJudge`, expected-trajectory matching.
- **Agent checks** — premature termination, runaway cost/steps, plan drift.
- **Dev UX** — `pytest` integration, JSON export + run-to-run diff, framework
  adapters (raw callable, Anthropic, OpenAI, LangChain).

## License

MIT
