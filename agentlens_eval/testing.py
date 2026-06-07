"""pytest helpers — run agentlens evals as normal tests.

This module imports `pytest` lazily, so importing `agentlens` itself never
requires pytest. Use it only in your test files.

Typical usage — one pytest row per case, with readable ids:

    from agentlens import Case, metrics
    from agentlens.testing import parametrize, check

    DATASET = [
        Case("weather in NYC", [metrics.Contains("72")], name="weather"),
        Case("cancel my plan", [metrics.ToolWasCalled("cancel_plan")], name="cancel"),
    ]

    @parametrize(DATASET)
    def test_agent(case):
        check(my_agent, case).assert_passed()

Running `pytest` then shows one pass/fail line per case, and a failing metric
prints exactly which check failed and why.
"""

from __future__ import annotations

from typing import Any

from .evaluation import Eval, Case, CaseResult, AgentFn


def parametrize(dataset: list[Case], *, argname: str = "case"):
    """A `@pytest.mark.parametrize` over a list of Cases, with names as test ids."""
    import pytest  # lazy: only needed at test time

    ids = [c.name or f"case{i + 1}" for i, c in enumerate(dataset)]
    return pytest.mark.parametrize(argname, dataset, ids=ids)


def check(agent: AgentFn, case: Case) -> CaseResult:
    """Run a single case through an agent and return its CaseResult.

    Call `.assert_passed()` on the result inside your test.
    """
    name = getattr(agent, "__name__", "agent")
    return Eval(name, agent).run([case]).case_results[0]
