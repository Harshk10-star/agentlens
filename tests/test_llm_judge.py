"""Tests for the LLMJudge metric, using a fake client so no API key is needed.

LLMJudge accepts any object with `.messages.create(...)`, so we pass a stub that
returns a canned verdict. This proves the metric's logic without hitting the API.
"""

import json
from types import SimpleNamespace

from agentlens_eval import Tracer, metrics


def _fake_client(verdict: dict):
    """A stand-in for anthropic.Anthropic() that returns a fixed JSON verdict."""
    def create(**kwargs):
        block = SimpleNamespace(type="text", text=json.dumps(verdict))
        return SimpleNamespace(content=[block])
    return SimpleNamespace(messages=SimpleNamespace(create=create))


def _trace_with(output: str):
    tracer = Tracer("judge-test")
    with tracer.step() as step:
        step.result = output
    return tracer.trace


def test_judge_pass():
    client = _fake_client({"passed": True, "reason": "polite and correct"})
    result = metrics.LLMJudge("reply is polite", client=client).check(_trace_with("Happy to help!"))
    assert result.passed
    assert result.detail == ""  # no detail noise on a pass


def test_judge_fail_surfaces_reason():
    client = _fake_client({"passed": False, "reason": "the reply is rude"})
    result = metrics.LLMJudge("reply is polite", client=client).check(_trace_with("go away"))
    assert not result.passed
    assert "rude" in result.detail


def test_judge_handles_api_errors_gracefully():
    def boom(**kwargs):
        raise RuntimeError("network down")
    client = SimpleNamespace(messages=SimpleNamespace(create=boom))
    result = metrics.LLMJudge("anything", client=client).check(_trace_with("whatever"))
    assert not result.passed
    assert "judge error" in result.detail  # failure is reported, not raised
