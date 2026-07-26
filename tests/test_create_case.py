import json
from contextlib import contextmanager

import pytest

from agent.tools.create_case import REVIEW_ID_FIELD, CreateCaseError, run


class FakeSupabaseResponse:
    def __init__(self, data):
        self.data = data


class FakeSupabaseTable:
    def __init__(self, data):
        self._data = data

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        return FakeSupabaseResponse(self._data)


class FakeSupabaseClient:
    def __init__(self, data):
        self._data = data

    def table(self, _name):
        return FakeSupabaseTable(self._data)


REVIEW_ROW = {
    "id": "r1",
    "rating": 1,
    "text": "Vi väntade en timme och personalen var otrevlig.",
    "source": "google",
    "created_at": "2026-07-01T10:00:00Z",
    "restaurants": {"name": "Fiktiva Kroken", "area": "Söder"},
    "review_analysis": None,
}


class FakeSalesforceResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


class FakeSalesforceClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return self._responses.pop(0)

    def instance_url(self):
        return "https://example-org.my.salesforce.com"


class FakeSpan:
    def __init__(self):
        self.updates = []

    def update(self, **fields):
        self.updates.append(fields)


class FakeTraceHandle:
    def __init__(self):
        self.spans = []
        self.outcomes = []

    @contextmanager
    def span(self, name, **fields):
        s = FakeSpan()
        self.spans.append((name, fields, s))
        yield s

    @contextmanager
    def generation(self, name, *, model, **fields):
        s = FakeSpan()
        self.spans.append((name, fields, s))
        yield s

    def set_outcome(self, *, tags=None, metadata=None):
        self.outcomes.append({"tags": tags, "metadata": metadata})


class FakeTracer:
    def __init__(self):
        self.traces = []

    @contextmanager
    def trace(self, name, **attrs):
        handle = FakeTraceHandle()
        self.traces.append((name, attrs, handle))
        yield handle

    def flush(self):
        pass


def test_high_severity_creates_case_with_correct_field_mapping():
    sf = FakeSalesforceClient([FakeSalesforceResponse(201, {"id": "500xa", "success": True, "errors": []})])

    raw = run(
        "r1",
        severity="high",
        draft_response="Tack för din feedback, vi ber om ursäkt för väntetiden.",
        reasoning="Lång väntan och otrevligt bemötande.",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result == {
        "review_id": "r1",
        "status": "created",
        "case_id": "500xa",
        "case_url": "https://example-org.my.salesforce.com/lightning/r/Case/500xa/view",
    }

    assert len(sf.calls) == 1
    method, path, kwargs = sf.calls[0]
    assert method == "PATCH"
    assert path == f"/sobjects/Case/{REVIEW_ID_FIELD}/r1"

    payload = kwargs["json"]
    assert payload["Subject"] == "[Gästpuls] Fiktiva Kroken: negative review (1/5)"
    assert payload["Priority"] == "High"
    # Salesforce rejects an upsert PATCH that repeats the external ID field
    # in the body — the review_id lives in the URL only.
    assert REVIEW_ID_FIELD not in payload
    assert "otrevlig" in payload["Description"]
    assert "Tack för din feedback" in payload["Description"]
    assert "review_id" not in payload["Description"].lower()


def test_medium_severity_also_creates_a_case():
    sf = FakeSalesforceClient([FakeSalesforceResponse(201, {"id": "500xb", "success": True, "errors": []})])

    raw = run(
        "r1",
        severity="medium",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result["status"] == "created"
    (_, _, kwargs), = sf.calls
    assert kwargs["json"]["Priority"] == "Medium"


def test_low_severity_is_skipped_without_any_salesforce_call():
    sf = FakeSalesforceClient([])

    raw = run(
        "r1",
        severity="low",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result["status"] == "skipped"
    assert sf.calls == []


def test_second_call_for_same_review_updates_instead_of_duplicating():
    sf = FakeSalesforceClient([FakeSalesforceResponse(204)])

    raw = run(
        "r1",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result == {"review_id": "r1", "status": "updated"}
    assert len(sf.calls) == 1  # one upsert call — no separate dedup query, no POST

    method, path, _ = sf.calls[0]
    assert method == "PATCH"
    assert path == f"/sobjects/Case/{REVIEW_ID_FIELD}/r1"


def test_update_via_200_with_created_false_maps_to_updated():
    """Salesforce documents 204 (no body) for an upsert update, but has been
    observed live returning 200 with a body carrying "created": false
    instead. The status code alone isn't a reliable signal — the "created"
    field in the body is."""
    sf = FakeSalesforceClient(
        [FakeSalesforceResponse(200, {"id": "500existing", "success": True, "errors": [], "created": False})]
    )

    raw = run(
        "r1",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result == {
        "review_id": "r1",
        "status": "updated",
        "case_id": "500existing",
        "case_url": "https://example-org.my.salesforce.com/lightning/r/Case/500existing/view",
    }


def test_create_via_200_with_created_true_maps_to_created():
    """The inverse of the 200/created:false case — if Salesforce ever
    reports a creation via 200 instead of 201, the "created" field must
    still drive the outcome, not the status code."""
    sf = FakeSalesforceClient(
        [FakeSalesforceResponse(200, {"id": "500new", "success": True, "errors": [], "created": True})]
    )

    raw = run(
        "r1",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result["status"] == "created"
    assert result["case_id"] == "500new"


def test_200_response_missing_created_field_falls_back_to_status_code():
    """Defensive fallback for a body shape that omits "created" entirely —
    not observed, but status 200 (not 201) should still read as "updated"
    rather than crash or misreport."""
    sf = FakeSalesforceClient([FakeSalesforceResponse(200, {"id": "500xa", "success": True, "errors": []})])

    raw = run(
        "r1",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
    )
    result = json.loads(raw)

    assert result["status"] == "updated"


def test_upsert_keys_on_review_id_not_subject():
    """Two different reviews for the same restaurant/rating must not collapse
    into one Case — the bug this fix addresses. Each gets its own PATCH,
    keyed by its own review_id in the URL."""
    sf = FakeSalesforceClient(
        [
            FakeSalesforceResponse(201, {"id": "500xa", "success": True, "errors": []}),
            FakeSalesforceResponse(201, {"id": "500xb", "success": True, "errors": []}),
        ]
    )

    run(
        "review-a",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient({**REVIEW_ROW, "id": "review-a"}),
        salesforce_client=sf,
    )
    run(
        "review-b",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient({**REVIEW_ROW, "id": "review-b"}),
        salesforce_client=sf,
    )

    assert len(sf.calls) == 2
    paths = [call[1] for call in sf.calls]
    assert paths == [
        f"/sobjects/Case/{REVIEW_ID_FIELD}/review-a",
        f"/sobjects/Case/{REVIEW_ID_FIELD}/review-b",
    ]


def test_salesforce_error_on_upsert_raises_create_case_error():
    sf = FakeSalesforceClient(
        [
            FakeSalesforceResponse(
                400,
                [{"message": "Required fields are missing: [Origin]", "errorCode": "REQUIRED_FIELD_MISSING"}],
            )
        ]
    )

    with pytest.raises(CreateCaseError):
        run(
            "r1",
            severity="high",
            draft_response="...",
            reasoning="...",
            supabase_client=FakeSupabaseClient(REVIEW_ROW),
            salesforce_client=sf,
        )


def test_unknown_severity_raises_create_case_error_not_silent_skip():
    sf = FakeSalesforceClient([])

    with pytest.raises(CreateCaseError):
        run(
            "r1",
            severity="urgent",
            draft_response="...",
            reasoning="...",
            supabase_client=FakeSupabaseClient(REVIEW_ROW),
            salesforce_client=sf,
        )
    assert sf.calls == []


def test_created_outcome_is_recorded_on_the_trace():
    sf = FakeSalesforceClient([FakeSalesforceResponse(201, {"id": "500xa", "success": True, "errors": []})])
    tracer = FakeTracer()

    run(
        "r1",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
        tracer=tracer,
    )

    (trace_name, trace_attrs, handle), = tracer.traces
    assert trace_name == "create_case"
    assert trace_attrs["metadata"] == {"review_id": "r1", "severity": "high"}

    outcome_tags = [tag for outcome in handle.outcomes for tag in (outcome["tags"] or [])]
    assert "outcome:created" in outcome_tags
    outcome_metadata = {}
    for outcome in handle.outcomes:
        outcome_metadata.update(outcome["metadata"] or {})
    assert outcome_metadata["outcome"] == "created"
    assert outcome_metadata["restaurant"] == "Fiktiva Kroken"
    assert outcome_metadata["case_id"] == "500xa"


def test_updated_outcome_is_recorded_on_the_trace():
    sf = FakeSalesforceClient([FakeSalesforceResponse(204)])
    tracer = FakeTracer()

    run(
        "r1",
        severity="high",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
        tracer=tracer,
    )

    (_, _, handle), = tracer.traces
    outcome_tags = [tag for outcome in handle.outcomes for tag in (outcome["tags"] or [])]
    assert "outcome:updated" in outcome_tags


def test_skipped_outcome_is_recorded_on_the_trace_without_a_salesforce_call():
    sf = FakeSalesforceClient([])
    tracer = FakeTracer()

    run(
        "r1",
        severity="low",
        draft_response="...",
        reasoning="...",
        supabase_client=FakeSupabaseClient(REVIEW_ROW),
        salesforce_client=sf,
        tracer=tracer,
    )

    assert sf.calls == []
    (_, _, handle), = tracer.traces
    outcome_tags = [tag for outcome in handle.outcomes for tag in (outcome["tags"] or [])]
    assert "outcome:skipped" in outcome_tags
    assert handle.spans == []  # no salesforce.upsert_case span opened below threshold
