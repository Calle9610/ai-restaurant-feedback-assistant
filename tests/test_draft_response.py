import json
from dataclasses import dataclass

import pytest

from agent.tools.draft_response import DraftResponseError, run


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


@dataclass
class FakeToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class FakeResponse:
    content: list
    stop_reason: str = "tool_use"


class FakeAnthropicMessages:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class FakeAnthropicClient:
    def __init__(self, response):
        self.messages = FakeAnthropicMessages(response)


def _classification_response(severity="high", reasoning="Lång väntan och otrevligt bemötande.", draft="ok"):
    return FakeResponse(
        content=[
            FakeToolUseBlock(
                id="tu_1",
                name="submit_classification",
                input={"severity": severity, "reasoning": reasoning, "draft_response": draft},
            )
        ]
    )


def test_run_returns_severity_reasoning_and_draft():
    supabase_client = FakeSupabaseClient(REVIEW_ROW)
    anthropic_client = FakeAnthropicClient(
        _classification_response(draft="Tack för din feedback, vi tar detta på allvar.")
    )

    raw = run("r1", supabase_client=supabase_client, anthropic_client=anthropic_client, model="test-model")
    result = json.loads(raw)

    assert result["review_id"] == "r1"
    assert result["severity"] == "high"
    assert "Tack för din feedback" in result["draft_response"]


def test_prompt_includes_swedish_language_instruction():
    supabase_client = FakeSupabaseClient(REVIEW_ROW)
    anthropic_client = FakeAnthropicClient(_classification_response())

    run("r1", supabase_client=supabase_client, anthropic_client=anthropic_client, model="test-model")

    sent_prompt = anthropic_client.messages.calls[0]["messages"][0]["content"]
    assert "SWEDISH" in sent_prompt


def test_prompt_forces_the_classification_tool():
    supabase_client = FakeSupabaseClient(REVIEW_ROW)
    anthropic_client = FakeAnthropicClient(_classification_response())

    run("r1", supabase_client=supabase_client, anthropic_client=anthropic_client, model="test-model")

    call = anthropic_client.messages.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "submit_classification"}


@pytest.mark.parametrize("raw_severity", ["High", " medium ", "LOW", "Medium\n"])
def test_severity_is_normalized_regardless_of_casing_or_whitespace(raw_severity):
    supabase_client = FakeSupabaseClient(REVIEW_ROW)
    anthropic_client = FakeAnthropicClient(_classification_response(severity=raw_severity))

    raw = run("r1", supabase_client=supabase_client, anthropic_client=anthropic_client, model="test-model")
    result = json.loads(raw)

    assert result["severity"] == raw_severity.strip().lower()


def test_invalid_severity_raises_draft_response_error_not_silent_default():
    supabase_client = FakeSupabaseClient(REVIEW_ROW)
    anthropic_client = FakeAnthropicClient(_classification_response(severity="urgent"))

    with pytest.raises(DraftResponseError):
        run("r1", supabase_client=supabase_client, anthropic_client=anthropic_client, model="test-model")


def test_missing_field_raises_draft_response_error():
    response = FakeResponse(
        content=[
            FakeToolUseBlock(
                id="tu_1",
                name="submit_classification",
                input={"severity": "high", "reasoning": "..."},  # draft_response missing
            )
        ]
    )
    supabase_client = FakeSupabaseClient(REVIEW_ROW)
    anthropic_client = FakeAnthropicClient(response)

    with pytest.raises(DraftResponseError):
        run("r1", supabase_client=supabase_client, anthropic_client=anthropic_client, model="test-model")
