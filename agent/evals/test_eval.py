"""Smoke test for the eval runner — not a quality gate on model accuracy.
Requires a real AGENT_ANTHROPIC_API_KEY and makes real Anthropic calls, so
this lives outside tests/ (excluded from pyproject.toml's testpaths) and is
never picked up by CI's bare `pytest`. Run explicitly:

    pytest agent/evals/
    python -m agent.evals.run_eval
"""

from agent.evals.run_eval import run_eval


def test_eval_runs_and_classifies_every_case():
    report = run_eval()

    assert len(report.cases) == 14
    for case in report.cases:
        assert case.actual_severity in ("low", "medium", "high")
