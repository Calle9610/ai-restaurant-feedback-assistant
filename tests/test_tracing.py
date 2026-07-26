import pytest

from agent.tracing import NullTracer, calculate_cost_usd, get_tracer, usage_and_cost_fields


def test_get_tracer_is_null_tracer_when_keys_are_absent(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    assert isinstance(get_tracer(), NullTracer)


@pytest.mark.parametrize(
    "public_key,secret_key",
    [
        (None, "secret"),
        ("public", None),
        (None, None),
    ],
)
def test_get_tracer_is_null_tracer_unless_both_keys_are_set(monkeypatch, public_key, secret_key):
    if public_key is None:
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    else:
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", public_key)

    if secret_key is None:
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", secret_key)

    assert isinstance(get_tracer(), NullTracer)


def test_get_tracer_uses_langfuse_when_both_keys_are_set(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret")

    # Stub langfuse.get_client so this test never constructs a real client or
    # touches the network — it only checks that get_tracer() picks the
    # Langfuse-backed branch when configured.
    import langfuse

    monkeypatch.setattr(langfuse, "get_client", lambda: object())

    tracer = get_tracer()
    assert type(tracer).__name__ == "LangfuseTracer"


def test_null_tracer_trace_and_span_are_pure_no_ops():
    tracer = NullTracer()

    with tracer.trace("do-a-thing", tags=["t"], metadata={"k": "v"}, session_id="s1") as trace:
        with trace.span("step-1", input={"x": 1}) as span:
            span.update(output={"y": 2})
        with trace.generation("call-model", model="claude-haiku-4-5") as gen:
            gen.update(output="hello", usage_details={"input": 1, "output": 1})
        trace.set_outcome(tags=["outcome:done"], metadata={"outcome": "done"})

    tracer.flush()  # must not raise, must not touch the network


def test_calculate_cost_usd_known_model():
    cost = calculate_cost_usd("claude-haiku-4-5-20251001", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == pytest.approx(1.00 + 5.00)


def test_calculate_cost_usd_unknown_model_returns_none():
    assert calculate_cost_usd("some-future-model", input_tokens=100, output_tokens=100) is None


def test_usage_and_cost_fields_shape_for_known_model():
    fields = usage_and_cost_fields("claude-haiku-4-5", input_tokens=1000, output_tokens=500)
    assert fields["usage_details"] == {"input": 1000, "output": 500}
    assert fields["cost_details"]["total"] == pytest.approx((1000 * 1.00 + 500 * 5.00) / 1_000_000)


def test_usage_and_cost_fields_omits_cost_for_unknown_model():
    fields = usage_and_cost_fields("some-future-model", input_tokens=1000, output_tokens=500)
    assert fields["usage_details"] == {"input": 1000, "output": 500}
    assert "cost_details" not in fields
