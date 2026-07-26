from agent.evals.run_eval import EvalReport, score_case

ROW = {"review_id": "r1", "restaurant": "Fiktiva Kroken", "rating": 2}


def _row(expected_severity, expected_case):
    return {**ROW, "expected_severity": expected_severity, "expected_case": expected_case}


def test_severity_match_true_when_actual_equals_expected():
    result = score_case(_row("medium", True), actual_severity="medium")
    assert result.severity_match is True


def test_severity_match_false_when_actual_differs():
    result = score_case(_row("medium", True), actual_severity="high")
    assert result.severity_match is False


def test_case_decision_derived_from_actual_severity_via_threshold():
    # threshold is medium: low -> no case, medium/high -> case
    assert score_case(_row("low", False), actual_severity="low").actual_case is False
    assert score_case(_row("low", False), actual_severity="medium").actual_case is True
    assert score_case(_row("low", False), actual_severity="high").actual_case is True


def test_no_policy_deviation_when_expected_case_matches_threshold_of_expected_severity():
    # expected_severity=high -> threshold says case=True, and expected_case=True: consistent
    result = score_case(_row("high", True), actual_severity="high")
    assert result.policy_deviation is False


def test_policy_deviation_flagged_when_expected_case_disagrees_with_threshold():
    # expected_severity=high -> threshold says case=True, but labeler says expected_case=False
    result = score_case(_row("high", False), actual_severity="high")
    assert result.policy_deviation is True


def test_severity_accuracy_includes_policy_deviation_rows():
    # one clean row (severity match) + one policy-deviation row (severity miss)
    clean = score_case(_row("medium", True), actual_severity="medium")
    deviation = score_case(_row("high", False), actual_severity="medium")  # severity miss too
    report = EvalReport(model="test-model", session_id="s1", cases=[clean, deviation])

    assert report.severity_accuracy == 0.5  # 1/2 — deviation row still counted


def test_case_decision_accuracy_excludes_policy_deviation_rows():
    # clean row where the model's case decision is wrong
    clean_wrong = score_case(_row("high", True), actual_severity="low")  # case_match=False
    # policy-deviation row where the model's case decision "matches" only by
    # construction of the threshold (severity=high -> case=True != expected_case=False)
    deviation = score_case(_row("high", False), actual_severity="high")  # case_match=False, policy_deviation=True

    report = EvalReport(model="test-model", session_id="s1", cases=[clean_wrong, deviation])

    # Only the clean row is scoreable, so accuracy is 0/1, not 0/2 — the
    # deviation row must not be silently blamed on the model.
    assert report.case_decision_accuracy == 0.0
    assert len(report.policy_deviations) == 1


def test_case_decision_accuracy_is_none_when_every_row_is_a_policy_deviation():
    deviation = score_case(_row("high", False), actual_severity="high")
    report = EvalReport(model="test-model", session_id="s1", cases=[deviation])

    assert report.case_decision_accuracy is None
