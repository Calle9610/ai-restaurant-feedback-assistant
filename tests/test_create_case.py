import json

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
    assert payload[REVIEW_ID_FIELD] == "r1"
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
