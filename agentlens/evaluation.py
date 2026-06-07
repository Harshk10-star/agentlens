"""The eval runner: run an agent over a dataset and score each run.

You give it an `agent` — any callable that takes a case input and returns a
`Trace` (use a `Tracer` inside and return `tracer.trace`). For each case it runs
the agent, applies that case's metrics, and collects the results into a `Report`
you can print, assert on in CI, or render to HTML.

    from agentlens import Eval, Case, metrics

    def my_agent(question: str):
        tracer = Tracer("my-agent")
        ... # run your loop, recording steps
        return tracer.trace

    report = Eval("my-agent", my_agent).run([
        Case("weather in NYC", [metrics.Contains("72"), metrics.ToolWasCalled("get_weather")]),
        Case("cancel my plan", [metrics.ToolWasCalled("cancel")]),
    ])
    report.summary()
    assert report.pass_rate == 1.0   # gate CI on it
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .trace import Trace
from .metrics import Metric, MetricResult

# An agent is anything that turns a case input into a Trace.
AgentFn = Callable[[Any], Trace]


@dataclass
class Case:
    """One test case: an input plus the metrics it must satisfy."""

    input: Any
    expect: list[Metric]
    name: str = ""

    def label(self, index: int) -> str:
        return self.name or f"case {index + 1}"


@dataclass
class CaseResult:
    """The outcome of running one case."""

    case: Case
    trace: Trace | None
    results: list[MetricResult] = field(default_factory=list)
    error: str | None = None  # set if the agent itself threw

    @property
    def passed(self) -> bool:
        return self.error is None and all(r.passed for r in self.results)


@dataclass
class Report:
    """The outcome of an eval run over a whole dataset."""

    name: str
    case_results: list[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.case_results)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.case_results if c.passed)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def summary(self) -> None:
        """Print a human-readable summary to stdout."""
        print(f"\n{self.name}: {self.passed}/{self.total} cases passed "
              f"({self.pass_rate:.0%})")
        for i, cr in enumerate(self.case_results):
            mark = "PASS" if cr.passed else "FAIL"
            print(f"  [{mark}] {cr.case.label(i)}")
            if cr.error:
                print(f"         agent error: {cr.error}")
            for r in cr.results:
                if not r.passed:
                    print(f"         x {r.metric}: {r.detail}")


class Eval:
    """Runs an agent over a dataset of cases."""

    def __init__(self, name: str, agent: AgentFn) -> None:
        self.name = name
        self.agent = agent

    def run(self, dataset: list[Case]) -> Report:
        report = Report(name=self.name)
        for case in dataset:
            report.case_results.append(self._run_case(case))
        return report

    def _run_case(self, case: Case) -> CaseResult:
        try:
            trace = self.agent(case.input)
        except Exception as exc:  # the agent blew up — that's a failure, not a crash
            return CaseResult(case=case, trace=None, error=f"{type(exc).__name__}: {exc}")
        results = [metric.check(trace) for metric in case.expect]
        return CaseResult(case=case, trace=trace, results=results)
