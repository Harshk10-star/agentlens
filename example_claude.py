"""Instrumenting a REAL Claude agent with agentlens.

This is the copy-paste recipe for an actual API-backed agent: a manual Claude
tool-use loop (Anthropic SDK) with agentlens woven in. The agentlens lines are
identical to the fake-model examples — only the "ask the model" line is real.

Requirements:
    pip install anthropic
    set ANTHROPIC_API_KEY  (PowerShell: $env:ANTHROPIC_API_KEY = "sk-ant-...")

Run it:
    python example_claude.py

It prints the trace summary and writes report.html. The agentlens lines are
marked with  # <-- agentlens
"""

from __future__ import annotations

import os
import sys

from agentlens_eval import Tracer, detect_loops          # <-- agentlens
from agentlens_eval.report import generate_html           # <-- agentlens


# ----------------------------------------------------------------------
# Your tool: an ordinary function. agentlens doesn't touch it.
# ----------------------------------------------------------------------
def get_weather(city: str) -> str:
    # A real implementation would call a weather API; we fake the result.
    return f"72F and sunny in {city}"


TOOLS_IMPL = {"get_weather": get_weather}

# Tool schema the model sees. The description is prescriptive about WHEN to call
# it — recent Claude models reach for tools more conservatively, so this helps.
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


def run_claude_agent(question: str) -> None:
    import anthropic  # imported here so the file still imports without the SDK

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    tracer = Tracer("claude-weather-agent")          # <-- agentlens: make the notebook

    messages = [{"role": "user", "content": question}]

    # --- the agent loop: keep going until Claude stops calling tools ---
    while True:
        with tracer.step() as step:                  # <-- agentlens: one page per model turn
            response = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=1024,
                thinking={"type": "adaptive"},
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            step.tokens = response.usage.output_tokens   # <-- agentlens: real token usage

            # capture any text the model emitted this turn as the "thought"
            text = " ".join(b.text for b in response.content if b.type == "text").strip()
            if text:
                step.thought = text                  # <-- agentlens

            if response.stop_reason != "tool_use":
                # Claude is done — record the final answer and stop.
                step.result = text                   # <-- agentlens
                break

            # Claude wants to use one or more tools.
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    out = TOOLS_IMPL[block.name](**block.input)   # YOU run the tool
                    step.tool_call(block.name, block.input, result=out)  # <-- agentlens
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(out),
                    })
            messages.append({"role": "user", "content": tool_results})

    # --- turn the notebook into a report ---
    warnings = detect_loops(tracer.trace)            # <-- agentlens
    path = generate_html(tracer.trace, "report.html", warnings=warnings)   # <-- agentlens

    print(f"Steps   : {tracer.trace.total_steps}")
    print(f"Tokens  : {tracer.trace.total_tokens}")
    print(f"Answer  : {tracer.trace.final_output}")
    for w in warnings:
        print(f"  [{w.severity}] {w.message}")
    print(f"Report  : {path.resolve()}")


if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first "
                 '(PowerShell: $env:ANTHROPIC_API_KEY = "sk-ant-...").')
    try:
        import anthropic  # noqa: F401
    except ImportError:
        sys.exit("Install the SDK first:  pip install anthropic")

    run_claude_agent("What's the weather in NYC?")
