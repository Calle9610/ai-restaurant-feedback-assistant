import json

import pytest

from agent.tools.create_case import CreateCaseError, run


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
    def __init__(self, status_code, json_data):
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


NO_EXISTING_CASE = FakeSalesforceResponse(200, {"totalSize": 0, "done": True, "records": []})


def test_high_severity_creates_case_with_correct_field_mapping():
    sf = FakeSalesforceClient(
        [NO_EXISTING_CASE, FakeSalesforceResponse(201, {"id": "500xa", "success": True, "errors": []})]
    )

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

    query_call, create_call = sf.calls
    assert query_call[0] == "GET"
    assert create_call[0] == "POST"
    assert create_call[1] == "/sobjects/Case"

    payload = create_call[2]["json"]
    assert payload["Subject"] == "[Gästpuls] Fiktiva Kroken: negative review (1/5)"
    assert payload["Priority"] == "High"
    assert "otrevlig" in payload["Description"]
    assert "Tack för din feedback" in payload["Description"]


def test_medium_severity_also_creates_a_case():
    sf = FakeSalesforceClient(
        [NO_EXISTING_CASE, FakeSalesforceResponse(201, {"id": "500xb", "success": True, "errors": []})]
    )

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
    _, create_call = sf.calls
    assert create_call[2]["json"]["Priority"] == "Medium"


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


def test_duplicate_subject_returns_already_exists_without_creating():
    sf = FakeSalesforceClient(
        [FakeSalesforceResponse(200, {"totalSize": 1, "done": True, "records": [{"Id": "500existing"}]})]
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

    assert result == {"review_id": "r1", "status": "already_exists", "case_id": "500existing"}
    assert len(sf.calls) == 1  # only the dedup query — no POST


def test_salesforce_error_on_create_raises_create_case_error():
    sf = FakeSalesforceClient(
        [
            NO_EXISTING_CASE,
            FakeSalesforceResponse(
                400,
                [{"message": "Required fields are missing: [Origin]", "errorCode": "REQUIRED_FIELD_MISSING"}],
            ),
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
