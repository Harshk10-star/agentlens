"""A runnable demo of agentlens.

We fake a small agent run that gets stuck in a loop, then generate an HTML
report. Run it:

    python example.py

It writes report.html next to this file. Open it in your browser.
"""

from agentlens_eval import Tracer, detect_loops
from agentlens_eval.report import generate_html


def main() -> None:
    tracer = Tracer("weather-agent demo")

    # A healthy first step.
    with tracer.step("user asked for the weather in NYC") as step:
        step.tool_call("get_weather", {"city": "NYC"},
                       result={"temp_f": 72}, tokens=120, latency_ms=820)

    # Now the agent gets stuck: same call, same args, three times in a row.
    for _ in range(3):
        with tracer.step("hmm, did that work? let me try again") as step:
            step.tool_call("get_weather", {"city": "NYC"},
                           result={"temp_f": 72}, tokens=118, latency_ms=790)

    # A step that errors.
    with tracer.step("try a different city") as step:
        step.tool_call("get_weather", {"city": "???"},
                       error="ValueError: unknown city", tokens=40, latency_ms=150)

    # Finally answers (no tool call this step, just reasoning + final output).
    with tracer.step("give up and answer with what we have") as step:
        step.result = "It's 72F in NYC."
        step.tokens = 60
        step.latency_ms = 410

    warnings = detect_loops(tracer.trace)
    path = generate_html(tracer.trace, "report.html", warnings=warnings)

    print(f"Steps recorded : {tracer.trace.total_steps}")
    print(f"Total tokens   : {tracer.trace.total_tokens}")
    print(f"Loop warnings  : {len(warnings)}")
    for w in warnings:
        print(f"  - [{w.severity}] {w.message}")
    print(f"\nReport written : {path.resolve()}")


if __name__ == "__main__":
    main()
