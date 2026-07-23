from dataclasses import dataclass

import pytest

from agent.loop import MaxIterationsError, run_loop


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class FakeResponse:
    content: list
    stop_reason: str


class FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        # Snapshot messages: run_loop mutates the same list object after
        # this call returns, so a bare reference would show later state.
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


def test_dispatches_tool_call_to_registry():
    responses = [
        FakeResponse(
            content=[FakeToolUseBlock(id="tu_1", name="echo", input={"text": "hej"})],
            stop_reason="tool_use",
        ),
        FakeResponse(content=[FakeTextBlock(text="hej")], stop_reason="end_turn"),
    ]
    client = FakeClient(responses)

    result = run_loop("say hej", model="test-model", client=client)

    assert result.final_text == "hej"
    tool_result_message = client.messages.calls[1]["messages"][-1]
    assert tool_result_message["content"][0]["tool_use_id"] == "tu_1"
    assert tool_result_message["content"][0]["content"] == "hej"


def test_unknown_tool_name_returns_error_to_model_not_crash():
    responses = [
        FakeResponse(
            content=[FakeToolUseBlock(id="tu_1", name="not_a_real_tool", input={})],
            stop_reason="tool_use",
        ),
        FakeResponse(content=[FakeTextBlock(text="ok")], stop_reason="end_turn"),
    ]
    client = FakeClient(responses)

    result = run_loop("do something", model="test-model", client=client)

    assert result.final_text == "ok"
    tool_result = client.messages.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "not_a_real_tool" in tool_result["content"]


def test_tool_exception_is_caught_and_reported_structurally():
    responses = [
        FakeResponse(
            content=[
                FakeToolUseBlock(id="tu_1", name="echo", input={"not_text": "x"})
            ],
            stop_reason="tool_use",
        ),
        FakeResponse(content=[FakeTextBlock(text="handled")], stop_reason="end_turn"),
    ]
    client = FakeClient(responses)

    result = run_loop("trigger a tool error", model="test-model", client=client)

    assert result.final_text == "handled"
    tool_result = client.messages.calls[1]["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "TypeError" in tool_result["content"]


def test_max_iterations_raises_with_message_history():
    responses = [
        FakeResponse(
            content=[FakeToolUseBlock(id=f"tu_{i}", name="echo", input={"text": "x"})],
            stop_reason="tool_use",
        )
        for i in range(3)
    ]
    client = FakeClient(responses)

    with pytest.raises(MaxIterationsError) as exc_info:
        run_loop("loop forever", model="test-model", client=client, max_iterations=3)

    error = exc_info.value
    assert error.max_iterations == 3
    assert len(error.messages) > 0
    # the transcript must actually contain the tool result for the last call
    found_last_tool_result = any(
        isinstance(item, dict) and item.get("tool_use_id") == "tu_2"
        for msg in error.messages
        if isinstance(msg.get("content"), list)
        for item in msg["content"]
    )
    assert found_last_tool_result


def test_parallel_tool_calls_map_results_to_correct_tool_use_id():
    responses = [
        FakeResponse(
            content=[
                FakeToolUseBlock(id="tu_a", name="echo", input={"text": "first"}),
                FakeToolUseBlock(id="tu_b", name="echo", input={"text": "second"}),
            ],
            stop_reason="tool_use",
        ),
        FakeResponse(content=[FakeTextBlock(text="done")], stop_reason="end_turn"),
    ]
    client = FakeClient(responses)

    run_loop("do two things at once", model="test-model", client=client)

    tool_results = client.messages.calls[1]["messages"][-1]["content"]
    by_id = {r["tool_use_id"]: r["content"] for r in tool_results}
    assert by_id == {"tu_a": "first", "tu_b": "second"}
