"""How to EVALUATE an agent with agentlens.

This is the step beyond tracing: we define a dataset of cases, each with the
checks it must pass, run a (fake) agent over all of them, and get a pass/fail
report you could gate CI on.

Run it:

    python example_eval.py

Then open eval_report.html.
"""

from agentlens_eval import Tracer, Eval, Case, metrics
from agentlens_eval.report import generate_eval_html


# ----------------------------------------------------------------------
# Your tools + a fake "model", same idea as example_my_agent.py.
# ----------------------------------------------------------------------
def get_weather(city: str) -> str:
    return f"72F and sunny in {city}"


def cancel_plan() -> str:
    return "Your plan has been cancelled."


# A trivially-scripted agent: it picks a tool based on the question, runs it,
# and returns the result. Returns a Trace so agentlens can score it.
def my_agent(question: str):
    tracer = Tracer("support-agent")
    with tracer.step(f"handling: {question}") as step:
        if "weather" in question:
            step.tool_call("get_weather", {"city": "NYC"},
                           result=get_weather("NYC"), tokens=120)
        elif "cancel" in question:
            step.tool_call("cancel_plan", {}, result=cancel_plan(), tokens=90)
        else:
            step.result = "Sorry, I can't help with that."
            step.tokens = 40
    return tracer.trace


# ----------------------------------------------------------------------
# The dataset: each Case is an input + the checks it must satisfy.
# ----------------------------------------------------------------------
dataset = [
    Case("what's the weather in NYC?",
         [metrics.Contains("72"), metrics.ToolWasCalled("get_weather")],
         name="weather lookup"),
    Case("please cancel my plan",
         [metrics.ToolWasCalled("cancel_plan"), metrics.Contains("cancelled")],
         name="cancellation"),
    Case("tell me a joke",
         [metrics.MaxSteps(3), metrics.NoErrors()],
         name="out-of-scope request"),
    # This one is designed to FAIL, to show what a failure looks like:
    Case("what's the weather?",
         [metrics.Contains("rain")],   # our agent never says "rain"
         name="(intentional fail)"),
]


if __name__ == "__main__":
    report = Eval("support-agent", my_agent).run(dataset)
    report.summary()
    path = generate_eval_html(report, "eval_report.html")
    print(f"\nReport written: {path.resolve()}")

    # This is the line that makes it useful in CI:
    # assert report.pass_rate == 1.0
