"""Unit tests for the deterministic metrics (agentlens.metrics).

The LLM-as-judge metric is covered separately in test_llm_judge.py; everything
here is free and offline. Each metric is checked on both a passing and a
failing trace, and we assert the failure `detail` is populated (it's what shows
up in the report when a case fails).
"""

from agentlens import Tracer, metrics


def _answer(text, *, tokens=0):
    """A one-step trace whose final output is `text`."""
    tracer = Tracer("test-agent")
    with tracer.step("answer") as step:
        step.result = text
        step.tokens = tokens
    return tracer.trace


def test_contains_case_insensitive_by_default():
    assert metrics.Contains("SUNNY").check(_answer("72F and sunny")).passed
    res = metrics.Contains("rainy").check(_answer("72F and sunny"))
    assert not res.passed
    assert "did not contain" in res.detail


def test_contains_case_sensitive():
    assert not metrics.Contains("SUNNY", case_sensitive=True).check(_answer("sunny")).passed
    assert metrics.Contains("sunny", case_sensitive=True).check(_answer("sunny")).passed


def test_regex():
    assert metrics.Regex(r"\d{2}F").check(_answer("it is 72F")).passed
    assert not metrics.Regex(r"\d{2}F").check(_answer("warm")).passed


def test_equals():
    assert metrics.Equals("exactly this").check(_answer("exactly this")).passed
    res = metrics.Equals("exactly this").check(_answer("something else"))
    assert not res.passed
    assert "expected" in res.detail


def test_tool_was_called():
    tracer = Tracer("a")
    with tracer.step() as step:
        step.tool_call("get_weather", {"city": "NYC"}, result="72F")
    trace = tracer.trace

    assert metrics.ToolWasCalled("get_weather").check(trace).passed
    res = metrics.ToolWasCalled("cancel_plan").check(trace)
    assert not res.passed
    assert "never called" in res.detail


def test_max_steps():
    tracer = Tracer("a")
    for _ in range(3):
        with tracer.step():
            pass
    trace = tracer.trace

    assert metrics.MaxSteps(3).check(trace).passed
    assert not metrics.MaxSteps(2).check(trace).passed


def test_max_tokens():
    assert metrics.MaxTokens(100).check(_answer("hi", tokens=80)).passed
    res = metrics.MaxTokens(50).check(_answer("hi", tokens=80))
    assert not res.passed
    assert "80 tokens" in res.detail


def test_no_errors():
    tracer = Tracer("a")
    with tracer.step() as step:
        step.tool_call("boom", {}, error="ValueError: nope")
    assert not metrics.NoErrors().check(tracer.trace).passed
    assert metrics.NoErrors().check(_answer("fine")).passed


def test_no_loops():
    looping = Tracer("a")
    with looping.step() as s:
        s.tool_call("search", {"q": "x"})
    with looping.step() as s:
        s.tool_call("search", {"q": "x"})
    assert not metrics.NoLoops().check(looping.trace).passed
    assert metrics.NoLoops().check(_answer("clean")).passed


def test_metric_str_is_used_as_result_name():
    # The report keys off str(metric); make sure it round-trips.
    res = metrics.Contains("72").check(_answer("72F"))
    assert res.metric == 'Contains("72")'
