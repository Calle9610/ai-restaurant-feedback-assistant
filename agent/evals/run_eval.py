"""Eval runner for the M9 eval set (agent/evals/dataset.json).

Classifies each labeled review via draft_response.run() only — create_case.run()
is never called, so no Case is ever written to Salesforce during an eval run.

Reports three numbers, kept deliberately separate:
  - severity accuracy: the model's severity vs. facit's expected_severity.
  - Case-decision accuracy: the threshold-derived decision (applied to the
    model's actual severity) vs. facit's expected_case — the number that
    matters most, since it's what would actually drive a Salesforce write.
  - policy deviations: rows where facit's expected_case disagrees with the
    threshold applied to facit's own expected_severity. These say the
    threshold policy is wrong for that case, not that the model got
    anything wrong — reported separately, never folded into either accuracy
    number.

Ground truth (expected_severity / expected_case) is set by a human in
dataset.json, never by this runner or by the model being evaluated.

Not run in CI: lives outside tests/ (pyproject.toml's testpaths excludes
it from a bare `pytest`) and requires a real AGENT_ANTHROPIC_API_KEY. Run
explicitly:
    python -m agent.evals.run_eval [--model ...] [--session-id ...]
    pytest agent/evals/
"""

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from agent.anthropic_client import get_model
from agent.tools import draft_response
from agent.tools.create_case import CASE_CREATION_THRESHOLD, SEVERITY_ORDER
from agent.tracing import get_tracer

DATASET_PATH = Path(__file__).parent / "dataset.json"


def _case_decision(severity: str) -> bool:
    return SEVERITY_ORDER[severity] >= SEVERITY_ORDER[CASE_CREATION_THRESHOLD]


@dataclass
class CaseResult:
    review_id: str
    restaurant: str
    rating: int
    expected_severity: str
    actual_severity: str
    expected_case: bool
    actual_case: bool
    severity_match: bool
    case_match: bool
    policy_deviation: bool


@dataclass
class EvalReport:
    model: str
    session_id: str
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def severity_accuracy(self) -> float:
        return sum(c.severity_match for c in self.cases) / len(self.cases)

    @property
    def case_decision_accuracy(self) -> float | None:
        # Excludes policy-deviation rows: by construction, expected_case on
        # those rows disagrees with the threshold applied to expected_severity
        # itself, so no severity the model could output makes actual_case
        # equal expected_case except by coincidence. Scoring them here would
        # count a policy problem as a model problem.
        scoreable = [c for c in self.cases if not c.policy_deviation]
        if not scoreable:
            return None
        return sum(c.case_match for c in scoreable) / len(scoreable)

    @property
    def policy_deviations(self) -> list[CaseResult]:
        return [c for c in self.cases if c.policy_deviation]


def score_case(row: dict, actual_severity: str) -> CaseResult:
    """Pure scoring logic, factored out of run_eval() so it's unit-testable
    without mocking draft_response/Supabase/Anthropic — row is one
    dataset.json entry, actual_severity is whatever draft_response returned.
    """
    expected_severity = row["expected_severity"]
    expected_case = row["expected_case"]
    actual_case = _case_decision(actual_severity)

    return CaseResult(
        review_id=row["review_id"],
        restaurant=row["restaurant"],
        rating=row["rating"],
        expected_severity=expected_severity,
        actual_severity=actual_severity,
        expected_case=expected_case,
        actual_case=actual_case,
        severity_match=actual_severity == expected_severity,
        case_match=actual_case == expected_case,
        policy_deviation=expected_case != _case_decision(expected_severity),
    )


def _load_dataset(dataset_path: Path) -> list[dict]:
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    unlabeled = [
        row["review_id"] for row in dataset if row["expected_severity"] is None or row["expected_case"] is None
    ]
    if unlabeled:
        raise ValueError(f"Dataset has unlabeled row(s), eval cannot proceed: {unlabeled}")
    return dataset


def run_eval(
    dataset_path: Path = DATASET_PATH,
    model: str | None = None,
    session_id: str | None = None,
) -> EvalReport:
    dataset = _load_dataset(dataset_path)

    resolved_model = get_model(model)
    resolved_session_id = session_id or f"eval-{int(time.time())}"
    tracer = get_tracer()

    cases = []
    for row in dataset:
        result = json.loads(
            draft_response.run(
                row["review_id"],
                model=resolved_model,
                tracer=tracer,
                session_id=resolved_session_id,
            )
        )
        cases.append(score_case(row, result["severity"]))

    tracer.flush()
    return EvalReport(model=resolved_model, session_id=resolved_session_id, cases=cases)


def print_report(report: EvalReport) -> None:
    print(f"model: {report.model}")
    print(f"session_id: {report.session_id}")
    print()

    print(
        f"{'review_id':10} {'restaurant':<20} {'rating':6} {'exp_sev':8} {'act_sev':8} "
        f"{'sev':4} {'exp_case':9} {'act_case':9} {'case':4} {'policy':6}"
    )
    for c in report.cases:
        print(
            f"{c.review_id[:8]:10} {c.restaurant:<20} {c.rating:<6} {c.expected_severity:<8} "
            f"{c.actual_severity:<8} {'OK' if c.severity_match else 'X':4} "
            f"{str(c.expected_case):<9} {str(c.actual_case):<9} {'OK' if c.case_match else 'X':4} "
            f"{'DEV' if c.policy_deviation else '':6}"
        )

    print()
    n = len(report.cases)
    print(f"severity accuracy:      {report.severity_accuracy:.0%} ({sum(c.severity_match for c in report.cases)}/{n})")

    scoreable = [c for c in report.cases if not c.policy_deviation]
    if report.case_decision_accuracy is None:
        print("case-decision accuracy: n/a (every row is a policy deviation)")
    else:
        excluded_note = f", {len(report.policy_deviations)} policy-deviation row(s) excluded" if report.policy_deviations else ""
        print(
            f"case-decision accuracy: {report.case_decision_accuracy:.0%} "
            f"({sum(c.case_match for c in scoreable)}/{len(scoreable)}{excluded_note})"
        )

    deviations = report.policy_deviations
    if deviations:
        print(
            f"\npolicy deviations ({len(deviations)}) — facit's expected_case disagrees with "
            "the threshold applied to facit's own expected_severity. These indict the "
            "threshold policy for that case, not the model:"
        )
        for c in deviations:
            print(f"  {c.review_id[:8]} {c.restaurant} — expected_severity={c.expected_severity}, expected_case={c.expected_case}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the M9 eval set against draft_response.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--model", default=None, help="Override AGENT_MODEL for this eval run.")
    parser.add_argument("--session-id", default=None, help="Langfuse session ID; auto-generated if omitted.")
    args = parser.parse_args()

    report = run_eval(dataset_path=args.dataset, model=args.model, session_id=args.session_id)
    print_report(report)


if __name__ == "__main__":
    main()
