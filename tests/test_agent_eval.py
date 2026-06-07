"""Example pytest suite for an agent — run with:  pytest

Each Case becomes its own test row. This file is self-contained (a fake agent)
so it passes out of the box; swap in your real agent to use it for real.
"""

from agentlens_eval import Tracer, Case, metrics
from agentlens_eval.testing import parametrize, check


# --- the agent under test (fake model, no API key needed) ----------------
def support_agent(question: str):
    tracer = Tracer("support-agent")
    with tracer.step(f"handling: {question}") as step:
        if "weather" in question:
            step.tool_call("get_weather", {"city": "NYC"},
                           result="72F and sunny in NYC", tokens=120)
        elif "cancel" in question:
            step.tool_call("cancel_plan", {}, result="Your plan has been cancelled.", tokens=90)
        else:
            step.result = "Sorry, I can't help with that."
            step.tokens = 40
    return tracer.trace


# --- the dataset: input + the checks each case must pass -----------------
DATASET = [
    Case("what's the weather in NYC?",
         [metrics.Contains("72"), metrics.ToolWasCalled("get_weather"), metrics.NoLoops()],
         name="weather-lookup"),
    Case("please cancel my plan",
         [metrics.ToolWasCalled("cancel_plan"), metrics.Contains("cancelled")],
         name="cancellation"),
    Case("tell me a joke",
         [metrics.MaxSteps(3), metrics.NoErrors(), metrics.MaxTokens(500)],
         name="out-of-scope"),
]


# --- one pytest row per case ---------------------------------------------
@parametrize(DATASET)
def test_support_agent(case):
    check(support_agent, case).assert_passed()
