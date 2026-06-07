"""Metrics — cheap, deterministic checks you run against an agent's trace.

A metric reads a finished `Trace` and returns pass/fail. These are all
assertion-style (no LLM calls), so they're fast, free, and reproducible — the
opposite of flaky. An optional LLM-as-judge metric can be layered on later.

    from agentlens import metrics

    checks = [
        metrics.Contains("72"),          # final answer contains "72"
        metrics.ToolWasCalled("get_weather"),
        metrics.MaxSteps(5),
        metrics.NoLoops(),
    ]
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .trace import Trace
from .detectors import detect_loops


@dataclass
class MetricResult:
    """The outcome of one metric against one trace."""

    metric: str
    passed: bool
    detail: str = ""


class Metric(ABC):
    """Base class. Subclass and implement `check`."""

    @property
    def name(self) -> str:
        return type(self).__name__

    @abstractmethod
    def check(self, trace: Trace) -> MetricResult: ...

    # small helper so subclasses stay terse
    def _result(self, passed: bool, detail: str = "") -> MetricResult:
        return MetricResult(metric=str(self), passed=passed, detail=detail)


# --- output metrics ------------------------------------------------------
class Contains(Metric):
    """Final answer contains `text`."""

    def __init__(self, text: str, *, case_sensitive: bool = False) -> None:
        self.text = text
        self.case_sensitive = case_sensitive

    def __str__(self) -> str:
        return f'Contains("{self.text}")'

    def check(self, trace: Trace) -> MetricResult:
        out = str(trace.final_output or "")
        hay, needle = (out, self.text) if self.case_sensitive else (out.lower(), self.text.lower())
        ok = needle in hay
        return self._result(ok, "" if ok else f"final output did not contain {self.text!r}")


class Regex(Metric):
    """Final answer matches `pattern` (re.search)."""

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern

    def __str__(self) -> str:
        return f'Regex("{self.pattern}")'

    def check(self, trace: Trace) -> MetricResult:
        ok = re.search(self.pattern, str(trace.final_output or "")) is not None
        return self._result(ok, "" if ok else f"no match for /{self.pattern}/")


class Equals(Metric):
    """Final answer equals `value` exactly."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def __str__(self) -> str:
        return f"Equals({self.value!r})"

    def check(self, trace: Trace) -> MetricResult:
        ok = trace.final_output == self.value
        return self._result(ok, "" if ok else f"got {trace.final_output!r}, expected {self.value!r}")


# --- trajectory metrics (the agent-aware part) ---------------------------
class ToolWasCalled(Metric):
    """The agent called tool `name` at some point."""

    def __init__(self, name: str) -> None:
        self.tool = name

    def __str__(self) -> str:
        return f'ToolWasCalled("{self.tool}")'

    def check(self, trace: Trace) -> MetricResult:
        ok = any(s.tool == self.tool for s in trace.steps)
        called = sorted({s.tool for s in trace.steps if s.tool})
        return self._result(ok, "" if ok else f"{self.tool!r} never called; called: {called}")


class MaxSteps(Metric):
    """The run used at most `n` steps (catches runaway agents)."""

    def __init__(self, n: int) -> None:
        self.n = n

    def __str__(self) -> str:
        return f"MaxSteps({self.n})"

    def check(self, trace: Trace) -> MetricResult:
        ok = trace.total_steps <= self.n
        return self._result(ok, "" if ok else f"took {trace.total_steps} steps (max {self.n})")


class MaxTokens(Metric):
    """The run used at most `n` tokens (catches runaway cost)."""

    def __init__(self, n: int) -> None:
        self.n = n

    def __str__(self) -> str:
        return f"MaxTokens({self.n})"

    def check(self, trace: Trace) -> MetricResult:
        ok = trace.total_tokens <= self.n
        return self._result(ok, "" if ok else f"used {trace.total_tokens} tokens (max {self.n})")


class NoErrors(Metric):
    """No step raised an error."""

    def __str__(self) -> str:
        return "NoErrors()"

    def check(self, trace: Trace) -> MetricResult:
        errs = trace.errors
        return self._result(not errs, "" if not errs else f"{len(errs)} step(s) errored")


class NoLoops(Metric):
    """The agent did not get stuck repeating a tool call."""

    def __str__(self) -> str:
        return "NoLoops()"

    def check(self, trace: Trace) -> MetricResult:
        warnings = detect_loops(trace)
        return self._result(not warnings, "" if not warnings else warnings[0].message)
