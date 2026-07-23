import json

from agent.tools.get_context import fetch_context, run


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


ROW = {
    "id": "r1",
    "rating": 2,
    "text": "Maten var kall och vi fick vänta 40 minuter.",
    "source": "google",
    "created_at": "2026-07-01T10:00:00Z",
    "restaurants": {"name": "Fiktiva Kroken", "area": "Söder"},
    "review_analysis": {
        "sentiment": "negative",
        "category": "food",
        "summary": "Kall mat, lång väntan.",
        "suggested_action": "Följ upp med köket.",
    },
}


def test_fetch_context_shapes_review_restaurant_and_analysis():
    context = fetch_context("r1", supabase_client=FakeSupabaseClient(ROW))

    assert context["review"] == {
        "id": "r1",
        "rating": 2,
        "text": "Maten var kall och vi fick vänta 40 minuter.",
        "source": "google",
        "created_at": "2026-07-01T10:00:00Z",
    }
    assert context["restaurant"] == {"name": "Fiktiva Kroken", "area": "Söder"}
    assert context["analysis"]["sentiment"] == "negative"
    assert context["analysis"]["category"] == "food"


def test_fetch_context_handles_missing_analysis():
    row = {**ROW, "review_analysis": None}

    context = fetch_context("r1", supabase_client=FakeSupabaseClient(row))

    assert context["analysis"] is None


def test_fetch_context_handles_list_shaped_one_to_one_embed():
    # Some PostgREST embeds come back as a single-item list rather than an object.
    row = {**ROW, "review_analysis": [ROW["review_analysis"]]}

    context = fetch_context("r1", supabase_client=FakeSupabaseClient(row))

    assert context["analysis"]["category"] == "food"


def test_fetch_context_handles_empty_list_shaped_embed():
    row = {**ROW, "review_analysis": []}

    context = fetch_context("r1", supabase_client=FakeSupabaseClient(row))

    assert context["analysis"] is None


def test_run_returns_json_string_matching_fetch_context():
    client = FakeSupabaseClient(ROW)

    raw = run("r1", supabase_client=client)
    parsed = json.loads(raw)

    assert parsed == fetch_context("r1", supabase_client=client)
