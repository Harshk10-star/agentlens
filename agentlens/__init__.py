"""agentlens — local-first observability + eval for AI agents.

Capture what your agent did (every step, tool call, token, and millisecond),
detect bad loops, and render it all to a self-contained HTML report. No backend,
no account, no cloud — it runs on your laptop.

Quick start:

    from agentlens import Tracer
    from agentlens.report import generate_html

    tracer = Tracer("my-agent")
    with tracer.step("decide what to do") as step:
        step.tool_call("get_weather", {"city": "NYC"}, result="72F",
                       tokens=120, latency_ms=800)

    path = generate_html(tracer.trace)   # -> writes report.html
"""

from .trace import Step, Trace, Tracer
from .detectors import detect_loops, LoopWarning
from .evaluation import Eval, Case, Report, CaseResult
from . import metrics

__all__ = [
    "Step", "Trace", "Tracer",
    "detect_loops", "LoopWarning",
    "Eval", "Case", "Report", "CaseResult",
    "metrics",
]
__version__ = "0.2.0"
