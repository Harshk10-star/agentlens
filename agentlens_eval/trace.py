"""Core data model: a Trace is a list of Steps; a Tracer records them.

Everything else in agentlens (loop detection, eval metrics, the HTML report)
reads from this one Trace object. One trace, many lenses.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import Any, Iterator, Optional


@dataclass
class Step:
    """A single iteration of the agent loop.

    A step optionally makes one tool call. `thought` is whatever the agent was
    reasoning about before acting (free text). Fields default to empty so a
    caller can record as much or as little as they have.
    """

    index: int
    thought: str = ""
    tool: Optional[str] = None
    args: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    tokens: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)

    def tool_call(
        self,
        tool: str,
        args: Optional[dict[str, Any]] = None,
        *,
        result: Any = None,
        tokens: int = 0,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> "Step":
        """Attach a tool call to this step. Returns self for chaining."""
        self.tool = tool
        self.args = args or {}
        self.result = result
        self.tokens = tokens
        self.latency_ms = latency_ms
        self.error = error
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Trace:
    """The full record of one agent run."""

    name: str = "agent-run"
    steps: list[Step] = field(default_factory=list)

    def add(self, step: Step) -> Step:
        self.steps.append(step)
        return step

    # --- aggregate views -------------------------------------------------
    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def total_tokens(self) -> int:
        return sum(s.tokens for s in self.steps)

    @property
    def total_latency_ms(self) -> float:
        return sum(s.latency_ms for s in self.steps)

    @property
    def errors(self) -> list[Step]:
        return [s for s in self.steps if s.error]

    @property
    def final_output(self) -> Any:
        """The result of the last step — i.e. the agent's final answer."""
        return self.steps[-1].result if self.steps else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total_steps": self.total_steps,
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "steps": [s.to_dict() for s in self.steps],
        }


class Tracer:
    """Records an agent run step by step.

    Use the `step()` context manager so latency is timed automatically:

        tracer = Tracer("my-agent")
        with tracer.step("figure out the weather") as step:
            step.tool_call("get_weather", {"city": "NYC"}, result="72F", tokens=120)
    """

    def __init__(self, name: str = "agent-run") -> None:
        self.trace = Trace(name=name)

    @contextmanager
    def step(self, thought: str = "") -> Iterator[Step]:
        step = Step(index=self.trace.total_steps + 1, thought=thought)
        self.trace.add(step)
        start = time.perf_counter()
        try:
            yield step
        except Exception as exc:  # record the failure, then re-raise
            step.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            # Only auto-fill latency if the caller didn't set it explicitly.
            if step.latency_ms == 0.0:
                step.latency_ms = (time.perf_counter() - start) * 1000
