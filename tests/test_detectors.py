"""Unit tests for loop detection (agentlens.detectors.detect_loops).

Covers both shapes the detector flags — back-to-back ("consecutive") and
repeated-anywhere ("frequent") — plus threshold tuning and the clean case.
"""

from agentlens import Tracer, detect_loops


def _trace(*calls):
    """Build a trace from (tool, args) pairs. None means a no-tool step."""
    tracer = Tracer("test-agent")
    for i, (tool, args) in enumerate(calls):
        with tracer.step(f"step {i}") as step:
            if tool is not None:
                step.tool_call(tool, args, result="ok", tokens=1)
            else:
                step.result = "done"
    return tracer.trace


def test_no_loops_when_args_differ():
    trace = _trace(("search", {"q": "a"}), ("search", {"q": "b"}))
    assert detect_loops(trace) == []


def test_consecutive_repeat_is_an_error():
    trace = _trace(("search", {"q": "x"}), ("search", {"q": "x"}))
    warnings = detect_loops(trace)

    assert len(warnings) == 1
    w = warnings[0]
    assert w.kind == "consecutive"
    assert w.severity == "error"
    assert w.count == 2
    assert w.step_indexes == [1, 2]
    assert "stuck in a loop" in w.message


def test_args_are_order_independent():
    # Same args, different key order — should still be seen as identical.
    trace = _trace(
        ("search", {"q": "x", "lang": "en"}),
        ("search", {"lang": "en", "q": "x"}),
    )
    warnings = detect_loops(trace)
    assert len(warnings) == 1
    assert warnings[0].kind == "consecutive"


def test_frequent_non_consecutive_repeat_is_a_warning():
    # Same call 3x but never back-to-back -> "frequent", severity warning.
    trace = _trace(
        ("search", {"q": "x"}),
        ("other", {}),
        ("search", {"q": "x"}),
        ("other", {}),
        ("search", {"q": "x"}),
    )
    warnings = detect_loops(trace)

    assert len(warnings) == 1
    w = warnings[0]
    assert w.kind == "frequent"
    assert w.severity == "warning"
    assert w.count == 3
    assert w.step_indexes == [1, 3, 5]
    assert "no progress" in w.message


def test_consecutive_not_double_reported_as_frequent():
    # 3x back-to-back is one consecutive error, not also a frequent warning.
    trace = _trace(
        ("search", {"q": "x"}),
        ("search", {"q": "x"}),
        ("search", {"q": "x"}),
    )
    warnings = detect_loops(trace)

    assert len(warnings) == 1
    assert warnings[0].kind == "consecutive"
    assert warnings[0].count == 3


def test_thresholds_are_configurable():
    trace = _trace(
        ("search", {"q": "x"}),
        ("other", {}),
        ("search", {"q": "x"}),
    )
    # Default frequent_threshold=3 -> nothing (only 2 repeats).
    assert detect_loops(trace) == []
    # Lower it to 2 -> flagged.
    warnings = detect_loops(trace, frequent_threshold=2)
    assert len(warnings) == 1
    assert warnings[0].kind == "frequent"


def test_steps_without_tools_are_ignored():
    trace = _trace((None, {}), (None, {}))
    assert detect_loops(trace) == []
