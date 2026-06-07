# 🔎 agentlens

Local-first **observability + eval** for AI agents.

Capture every step your agent takes — thoughts, tool calls, tokens, latency,
errors — automatically detect when it gets **stuck in a loop**, and render the
whole run to a self-contained **HTML report**. No backend, no account, no cloud.
The core is **stdlib-only**.

> On PyPI as [`agentlens-eval`](https://pypi.org/project/agentlens-eval/) (the
> bare `agentlens` name was taken); imports as `agentlens_eval`.

**Site:** a static landing page + docs live in [`site/`](site/) — open
`site/index.html` in a browser (no build step).

## Why

Most agent tools either (a) only score the final answer, missing mistakes that
happen mid-run, or (b) require a hosted dashboard (Postgres + ClickHouse, an
account, a cloud). `agentlens` is the opposite: **one trace object, many
lenses**, running entirely on your laptop.

## Install

```bash
pip install agentlens-eval        # then: import agentlens_eval
```

Or from source, for development:

```bash
pip install -e .
```

## Quick start

```python
from agentlens_eval import Tracer, detect_loops
from agentlens_eval.report import generate_html

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

## What's in the box (v0.3)

- **Tracing** — `Tracer` / `Step` / `Trace`; latency timed automatically.
- **Loop detection** — consecutive and frequent repeated tool calls.
- **HTML trace report** — timeline, per-step tool calls, totals, loop warnings.
- **Eval layer** — cheap, deterministic metrics (`Contains`, `Regex`, `Equals`,
  `ToolWasCalled`, `MaxSteps`, `MaxTokens`, `NoErrors`, `NoLoops`) plus an
  `Eval` / `Case` runner that produces a `pass_rate` you can gate CI on, and an
  HTML eval report with per-case pass/fail.
- **LLM-as-judge** — opt-in `LLMJudge("criteria")` for grading open-ended outputs
  with Claude. It's the only metric that costs tokens, so the rest of your suite
  stays cheap and deterministic.

```python
from agentlens_eval import Eval, Case, metrics

report = Eval("my-agent", my_agent).run([
    Case("weather in NYC", [metrics.Contains("72"), metrics.ToolWasCalled("get_weather")]),
])
report.summary()
assert report.pass_rate == 1.0   # CI gate
```

See `example_eval.py` for a full dataset.

### pytest integration

Run your evals as normal tests — one pass/fail row per case:

```python
from agentlens_eval import Case, metrics
from agentlens_eval.testing import parametrize, check

DATASET = [Case("weather in NYC", [metrics.Contains("72")], name="weather")]

@parametrize(DATASET)
def test_agent(case):
    check(my_agent, case).assert_passed()
```

```bash
pytest -v        # tests/test_agent_eval.py::test_agent[weather] PASSED
```

Or gate a whole run: `Eval(...).run(dataset).assert_passed(min_pass_rate=0.9)`.

## Roadmap

The whole design is layers over the same `Trace`:

- **More agent checks** — premature termination, plan drift, expected-trajectory match.
- **Dev UX** — JSON export + run-to-run regression diff, framework adapters (raw
  callable, Anthropic, OpenAI, LangChain), `agentlens.wrap(client)` one-line
  auto-capture.
- **Packaging** — publish to PyPI as `pip install agentlens-eval` (the bare
  `agentlens` name is taken, so the distribution is `agentlens-eval` while the
  import stays `agentlens_eval`).

## License

MIT
