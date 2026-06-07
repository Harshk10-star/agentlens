"""Loop / repetition detection over a Trace.

The classic agent failure mode: it calls the same tool with the same arguments
over and over, burning tokens without making progress. We flag two shapes:

  * consecutive repeats — the same (tool, args) back-to-back
  * frequent repeats — the same (tool, args) N+ times anywhere in the run
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .trace import Trace


@dataclass
class LoopWarning:
    """A detected repetition. `severity` is "warning" or "error"."""

    kind: str  # "consecutive" | "frequent"
    tool: str
    args: dict[str, Any]
    count: int
    step_indexes: list[int]
    severity: str = "warning"

    @property
    def message(self) -> str:
        args_preview = json.dumps(self.args, default=str)
        if len(args_preview) > 80:
            args_preview = args_preview[:77] + "..."
        if self.kind == "consecutive":
            return (
                f"`{self.tool}` called {self.count}x in a row with identical "
                f"args {args_preview} (steps {self._range}) — likely stuck in a loop"
            )
        return (
            f"`{self.tool}` called {self.count}x total with identical args "
            f"{args_preview} (steps {self._range}) — possible loop / no progress"
        )

    @property
    def _range(self) -> str:
        return ", ".join(str(i) for i in self.step_indexes)


def _key(tool: str, args: dict[str, Any]) -> str:
    """A stable signature for a (tool, args) pair, order-independent."""
    return tool + "::" + json.dumps(args, sort_keys=True, default=str)


def detect_loops(
    trace: Trace,
    *,
    consecutive_threshold: int = 2,
    frequent_threshold: int = 3,
) -> list[LoopWarning]:
    """Scan a trace for repeated tool calls.

    consecutive_threshold: back-to-back identical calls at/above this count are
        flagged as an "error" (almost certainly a stuck loop).
    frequent_threshold: identical calls anywhere at/above this count are flagged
        as a "warning".
    """
    warnings: list[LoopWarning] = []
    calls = [(s.index, s.tool, s.args) for s in trace.steps if s.tool]

    # --- consecutive repeats --------------------------------------------
    run_start = 0
    while run_start < len(calls):
        run_end = run_start
        base = _key(calls[run_start][1], calls[run_start][2])
        while run_end + 1 < len(calls) and _key(calls[run_end + 1][1], calls[run_end + 1][2]) == base:
            run_end += 1
        run_len = run_end - run_start + 1
        if run_len >= consecutive_threshold and run_len >= 2:
            _, tool, args = calls[run_start]
            warnings.append(
                LoopWarning(
                    kind="consecutive",
                    tool=tool,
                    args=args,
                    count=run_len,
                    step_indexes=[calls[i][0] for i in range(run_start, run_end + 1)],
                    severity="error",
                )
            )
        run_start = run_end + 1

    # --- frequent (non-consecutive) repeats -----------------------------
    seen: dict[str, list[int]] = {}
    meta: dict[str, tuple[str, dict[str, Any]]] = {}
    for idx, tool, args in calls:
        k = _key(tool, args)
        seen.setdefault(k, []).append(idx)
        meta[k] = (tool, args)
    already = {tuple(w.step_indexes) for w in warnings}
    for k, idxs in seen.items():
        if len(idxs) >= frequent_threshold and tuple(idxs) not in already:
            tool, args = meta[k]
            warnings.append(
                LoopWarning(
                    kind="frequent",
                    tool=tool,
                    args=args,
                    count=len(idxs),
                    step_indexes=idxs,
                    severity="warning",
                )
            )

    return warnings
