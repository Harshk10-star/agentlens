"""How to integrate agentlens into YOUR OWN agent loop.

This is a complete, runnable example of a typical "expose tools + loop" agent.
The model here is FAKE (a hardcoded script) so you can run it with no API key
and focus on the integration — the agentlens parts are identical no matter what
real model you swap in.

Run it:

    python example_my_agent.py

Then open report.html. Look for the loop warning — this fake agent gets stuck
calling the same tool, exactly like a real one can.

The only agentlens lines are marked with  # <-- agentlens
"""

from agentlens_eval import Tracer, detect_loops          # <-- agentlens
from agentlens_eval.report import generate_html           # <-- agentlens


# ----------------------------------------------------------------------
# 1. YOUR TOOLS — ordinary functions. agentlens doesn't touch these.
# ----------------------------------------------------------------------
def get_weather(city: str) -> str:
    return f"72F and sunny in {city}"


def search(query: str) -> str:
    return f"top result for '{query}'"


TOOLS = {"get_weather": get_weather, "search": search}


# ----------------------------------------------------------------------
# 2. A FAKE "model". In real life this is client.messages.create(...).
#    It just returns, each turn, what the agent should do next.
#    We script it to get stuck in a loop so the report has something to show.
# ----------------------------------------------------------------------
def fake_llm(turn: int) -> dict:
    script = [
        {"tool": "get_weather", "args": {"city": "NYC"}},   # turn 0
        {"tool": "get_weather", "args": {"city": "NYC"}},   # turn 1  (stuck...)
        {"tool": "get_weather", "args": {"city": "NYC"}},   # turn 2  (...still stuck)
        {"answer": "It's 72F in NYC."},                      # turn 3  (finally done)
    ]
    return script[min(turn, len(script) - 1)]


# ----------------------------------------------------------------------
# 3. YOUR AGENT LOOP — with agentlens woven in.
# ----------------------------------------------------------------------
def run_agent() -> None:
    tracer = Tracer("my-tool-agent")                 # <-- agentlens: make the notebook (once)

    turn = 0
    done = False
    while not done:
        with tracer.step() as step:                  # <-- agentlens: a "page" per loop iteration
            decision = fake_llm(turn)                # ask the model what to do

            if "tool" in decision:                   # the model wants to call a tool
                name, args = decision["tool"], decision["args"]
                result = TOOLS[name](**args)         # YOU run the tool
                step.tool_call(name, args, result=result)   # <-- agentlens: write down the call
                # (in a real loop you'd also append the result to your messages here)
            else:                                    # the model gave a final answer
                step.result = decision["answer"]     # <-- agentlens: record the final answer
                done = True

        turn += 1

    # ------------------------------------------------------------------
    # 4. Turn the notebook into a report.
    # ------------------------------------------------------------------
    warnings = detect_loops(tracer.trace)            # <-- agentlens: find stuck loops
    generate_html(tracer.trace, "report.html", warnings=warnings)   # <-- agentlens

    print(f"Done in {tracer.trace.total_steps} steps.")
    for w in warnings:
        print(f"  [{w.severity}] {w.message}")
    print("Open report.html to see the full trace.")


if __name__ == "__main__":
    run_agent()
