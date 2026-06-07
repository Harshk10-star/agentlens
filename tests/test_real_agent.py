"""Eval suite against a REAL Claude agent (opt-in, not run in CI).

Unlike the rest of the suite, these tests make live Anthropic API calls — so
they're slow, cost tokens, and aren't perfectly deterministic. They therefore
*skip themselves* unless you opt in:

    pip install anthropic
    $env:ANTHROPIC_API_KEY = "sk-ant-..."   # PowerShell
    python -m pytest tests/test_real_agent.py -v -m live

Without the key (e.g. in CI) every test here is skipped, so the default
`pytest` run stays fast, free, and green.

The pattern is identical to the fake-agent suite (test_agent_eval.py): an agent
is just `Callable[[input], Trace]`. Only the "ask the model" line is real.
"""

from __future__ import annotations

import os

import pytest

from agentlens import Case, Tracer, metrics
from agentlens.testing import check, parametrize

# Skip the whole module unless a key is present AND the SDK is installed.
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="set ANTHROPIC_API_KEY to run live agent tests",
    ),
]


# --- the tool the agent can call (an ordinary function) ------------------
def get_weather(city: str) -> str:
    return f"72F and sunny in {city}"


TOOLS_IMPL = {"get_weather": get_weather}
TOOL_SCHEMAS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Call this whenever "
                       "the user asks about weather or temperature.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    }
]


# --- the real agent: a Claude tool-use loop that returns a Trace ---------
def claude_agent(question: str):
    """Run one question through a live Claude tool-use loop, return the Trace."""
    import anthropic  # imported lazily so collection works without the SDK

    client = anthropic.Anthropic()
    tracer = Tracer("claude-weather-agent")
    messages = [{"role": "user", "content": question}]

    while True:
        with tracer.step() as step:
            resp = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=1024,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            step.tokens = resp.usage.output_tokens
            text = " ".join(b.text for b in resp.content if b.type == "text").strip()
            if text:
                step.thought = text

            if resp.stop_reason != "tool_use":
                step.result = text
                break

            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    out = TOOLS_IMPL[block.name](**block.input)
                    step.tool_call(block.name, block.input, result=out)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(out),
                    })
            messages.append({"role": "user", "content": tool_results})

    return tracer.trace


# --- the dataset: behavioural expectations, not exact-string matches -----
# Real model output varies, so prefer trajectory + contains checks over Equals.
DATASET = [
    Case(
        "What's the weather in NYC?",
        [
            metrics.ToolWasCalled("get_weather"),  # it actually used the tool
            metrics.Contains("72"),                # the tool's answer reached the user
            metrics.NoLoops(),                     # didn't get stuck
            metrics.MaxSteps(4),                   # didn't run away
        ],
        name="weather-nyc",
    ),
    Case(
        "Tell me a fun fact about the ocean.",
        [
            metrics.NoLoops(),
            metrics.NoErrors(),
            # Open-ended quality is the one place an LLM judge earns its cost:
            metrics.LLMJudge("The reply states at least one plausible, accurate fact about the ocean."),
        ],
        name="open-ended",
    ),
]


@parametrize(DATASET)
def test_claude_agent(case):
    check(claude_agent, case).assert_passed()
