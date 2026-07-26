"""Langfuse-backed tracing for the agent, with a no-op fallback.

No-op by construction: get_tracer() returns a NullTracer whenever
LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY aren't both set in the environment.
Nothing in this module imports or constructs a Langfuse client unless both
are present — the gate happens before any langfuse import, not by trusting
the SDK's own graceful-degradation behavior. CI and pytest never set these,
so every test run exercises NullTracer and makes zero network calls.

Tracer/TraceHandle/SpanHandle form a small duck-typed interface so callers
(agent/loop.py, draft_response.py, create_case.py) don't import langfuse
directly and tests can inject a fake tracer the same way they already inject
FakeSupabaseClient / FakeSalesforceClient.

Nesting: a trace opened while another is already active (e.g. draft_response
opening its own trace() call from inside agent/run.py's outer trace) nests
as a child span under Langfuse's ambient OpenTelemetry context automatically
— callers don't need to thread a parent reference by hand.
"""

from __future__ import annotations

import os
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Iterator, Protocol

# USD per million tokens. Source: Anthropic API pricing page
# (https://platform.claude.com/docs/en/pricing), current as of 2026-07-26.
# A hardcoded, undated rate goes silently stale when Anthropic revises
# prices — re-check this against the pricing page before trusting it months
# from now, and update the date comment when you do.
_MODEL_PRICE_PER_MTOK_USD: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}


def calculate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Deterministic cost calculation from the table above, rather than
    relying on Langfuse's own model-pricing catalog matching our exact model
    string. Returns None for a model not in the table (e.g. AGENT_MODEL
    overridden to something not yet priced here) instead of guessing.
    """
    pricing = _MODEL_PRICE_PER_MTOK_USD.get(model)
    if pricing is None:
        return None
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


def usage_and_cost_fields(model: str, input_tokens: int, output_tokens: int) -> dict[str, Any]:
    fields: dict[str, Any] = {"usage_details": {"input": input_tokens, "output": output_tokens}}
    cost = calculate_cost_usd(model, input_tokens, output_tokens)
    if cost is not None:
        fields["cost_details"] = {"total": cost}
    return fields


class SpanHandle(Protocol):
    def update(self, **fields: Any) -> None: ...


class TraceHandle(Protocol):
    def span(self, name: str, **fields: Any) -> AbstractContextManager[SpanHandle]: ...

    def generation(self, name: str, *, model: str, **fields: Any) -> AbstractContextManager[SpanHandle]: ...

    def set_outcome(self, *, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> None: ...


class Tracer(Protocol):
    def trace(
        self,
        name: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> AbstractContextManager[TraceHandle]: ...

    def flush(self) -> None: ...


# ---------------------------------------------------------------------------
# No-op implementation
# ---------------------------------------------------------------------------


class _NullSpan:
    def update(self, **fields: Any) -> None:
        pass


class _NullTrace:
    @contextmanager
    def span(self, name: str, **fields: Any) -> Iterator[_NullSpan]:
        yield _NullSpan()

    @contextmanager
    def generation(self, name: str, *, model: str, **fields: Any) -> Iterator[_NullSpan]:
        yield _NullSpan()

    def set_outcome(self, *, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> None:
        pass


class NullTracer:
    """Zero-import-side-effect tracer used whenever Langfuse isn't configured."""

    @contextmanager
    def trace(
        self,
        name: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> Iterator[_NullTrace]:
        yield _NullTrace()

    def flush(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Langfuse-backed implementation
# ---------------------------------------------------------------------------


class _LangfuseSpan:
    def __init__(self, observation: Any):
        self._observation = observation

    def update(self, **fields: Any) -> None:
        self._observation.update(**fields)


class _LangfuseTrace:
    def __init__(self, client: Any):
        self._client = client

    @contextmanager
    def span(self, name: str, **fields: Any) -> Iterator[_LangfuseSpan]:
        with self._client.start_as_current_observation(name=name, as_type="span", **fields) as obs:
            yield _LangfuseSpan(obs)

    @contextmanager
    def generation(self, name: str, *, model: str, **fields: Any) -> Iterator[_LangfuseSpan]:
        with self._client.start_as_current_observation(
            name=name, as_type="generation", model=model, **fields
        ) as obs:
            yield _LangfuseSpan(obs)

    def set_outcome(self, *, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> None:
        from langfuse import propagate_attributes

        with propagate_attributes(tags=tags, metadata=metadata):
            pass


class LangfuseTracer:
    """Wraps langfuse.get_client() — the SDK's own singleton accessor, so
    every call site in one process shares one client/OTel span processor
    instead of each constructing its own.
    """

    def __init__(self) -> None:
        from langfuse import get_client

        self._client = get_client()

    @contextmanager
    def trace(
        self,
        name: str,
        *,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> Iterator[_LangfuseTrace]:
        from langfuse import propagate_attributes

        with self._client.start_as_current_observation(name=name, as_type="span"):
            # trace_name deliberately not propagated here: it's a plain string
            # attribute that overwrites (not merges) on each nested call, so
            # draft_response's and create_case's own trace() calls would each
            # stomp the outer flow's name — last caller wins. Leaving it unset
            # lets Langfuse fall back to the actual root span's name instead.
            with propagate_attributes(tags=tags, metadata=metadata, session_id=session_id):
                yield _LangfuseTrace(self._client)

    def flush(self) -> None:
        self._client.flush()


def get_tracer() -> Tracer:
    if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
        return LangfuseTracer()
    return NullTracer()
