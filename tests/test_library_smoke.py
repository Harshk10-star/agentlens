from agentlens import Case, Eval, Tracer, detect_loops, metrics
from agentlens.report import generate_eval_html, generate_html


def _search_agent(question: str):
    tracer = Tracer("smoke-agent")
    with tracer.step("first lookup") as step:
        step.tool_call("search", {"q": question}, result="still looking", tokens=10)
    with tracer.step("retry same lookup") as step:
        step.tool_call("search", {"q": question}, result=f"answer for {question}", tokens=12)
    return tracer.trace


def test_public_api_trace_detect_report_and_eval(tmp_path):
    trace = _search_agent("weather")

    assert trace.total_steps == 2
    assert trace.total_tokens == 22
    assert trace.final_output == "answer for weather"

    warnings = detect_loops(trace)
    assert len(warnings) == 1
    assert warnings[0].kind == "consecutive"
    assert warnings[0].severity == "error"
    assert warnings[0].step_indexes == [1, 2]

    trace_path = generate_html(trace, tmp_path / "trace.html", warnings=warnings)
    trace_html = trace_path.read_text(encoding="utf-8")
    assert "agentlens trace report" in trace_html
    assert "likely stuck in a loop" in trace_html
    assert "answer for weather" in trace_html

    report = Eval("smoke-eval", _search_agent).run([
        Case(
            "weather",
            [metrics.ToolWasCalled("search"), metrics.Contains("answer for weather")],
            name="search-answer",
        )
    ])
    report.assert_passed()
    assert report.pass_rate == 1.0

    eval_path = generate_eval_html(report, tmp_path / "eval.html")
    eval_html = eval_path.read_text(encoding="utf-8")
    assert "agentlens eval report" in eval_html
    assert "search-answer" in eval_html
    assert "100%" in eval_html
