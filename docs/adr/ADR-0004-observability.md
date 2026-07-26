# ADR-0004: Langfuse for agent observability

- **Status:** Accepted
- **Date:** 2026-07-26
- **Context:** Gästpuls v2 (FDE case)

## Context

M9 needs every agent run to produce a trace: which tools were called, model
latency and token cost per step, and the outcome (Case created/updated/
skipped). This is both a real engineering need — the agent makes real
Anthropic and Salesforce API calls, and debugging a bad classification or a
failed upsert needs to see the actual prompt/response, not just a log line —
and the foundation two other pieces of M9 build on: the eval set (PR 3) needs
to group and filter runs by outcome, and the dashboard metrics view (PR 4)
needs aggregate cost/latency/success-rate numbers to display.

## Decision

Langfuse Cloud (free tier), wrapped behind a small `agent/tracing.py`
abstraction (`Tracer` / `TraceHandle` / `SpanHandle`) rather than importing
the Langfuse SDK directly in `agent/loop.py`, `draft_response.py`, and
`create_case.py`.

- **No-op by construction.** `get_tracer()` returns a `NullTracer` whenever
  `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` aren't both set — checked in
  our own code, before any `langfuse` import. CI and pytest never set these
  variables, so every test run exercises `NullTracer`: zero network calls,
  zero import-time side effects. `tests/test_tracing.py` and a dedicated test
  in `tests/test_loop.py` pin this contract explicitly rather than relying on
  it being incidentally true in this environment.
- **Trace-level metadata and tags, not just spans.** Each `--review-id` run
  is one Langfuse trace carrying `review_id`, `restaurant`, `severity`, and
  the final outcome (`created`/`updated`/`skipped`) as trace tags/metadata —
  set via Langfuse's `propagate_attributes()`, which attaches to the whole
  trace regardless of which nested span calls it. Without this, the
  Langfuse UI can only filter/aggregate by span name, not by "how many high-
  severity reviews became Cases this week" — exactly what PR 4's metrics view
  and PR 3's eval analysis need. `Tracer.trace()` also accepts an optional
  `session_id`, unused today but threaded all the way through
  `agent/run.py`'s `--session-id` flag — PR 3's eval runner can pass a shared
  session ID across many `--review-id` invocations to group them in the
  Langfuse UI without any interface change.
- **Deterministic cost calculation**, not Langfuse's model-pricing catalog.
  `agent/tracing.py` hardcodes Haiku 4.5's per-token rate in one named,
  dated constant (`_MODEL_PRICE_PER_MTOK_USD`, sourced from the Anthropic
  pricing page as of 2026-07-26) rather than trusting Langfuse to recognize
  our exact model string and apply the right rate. An undated hardcoded rate
  would go silently wrong the next time Anthropic revises prices; the date
  comment is the reminder to re-check it.
- **Ambient nesting, not manually-threaded parent spans.** Langfuse's v3 SDK
  is OpenTelemetry-based: a `tracer.trace(...)` call opened while another is
  already active nests as a child span of it automatically, via OTel's
  context-local "current span," rather than requiring an explicit parent
  reference to be passed down. `agent/run.py`'s `--review-id` path opens one
  outer trace; `draft_response.run()` and `create_case.run()` each open
  their own trace call, which nests under it rather than starting a second,
  disconnected trace — giving one coherent trace per CLI invocation.

## Alternatives considered

- **Cloud free tier vs. self-hosted Langfuse** — self-hosting means standing
  up and maintaining Postgres/ClickHouse/Redis containers for a demo that
  generates a handful of traces a day; the free tier covers far more than
  this project needs and ships the same trace-waterfall/cost UI with zero
  infrastructure. Self-hosting becomes the right call at a real customer with
  data-residency requirements — the same "next step in production" pattern
  ADR-0003 uses for Agentforce.
- **Generic OpenTelemetry + a generic backend** (Jaeger, Grafana Tempo, an
  APM vendor) — rejected because it would need either self-hosting a trace
  viewer or paying for general-purpose APM, and neither gives an
  LLM-specific view (token cost, prompt/completion pairs, model name per
  span) out of the box the way Langfuse does. Langfuse is itself built on
  OTel under the hood, so this isn't a capability gap, just extra
  infrastructure for no benefit here.
- **Custom logging table in Supabase** — rejected: this would mean building
  our own trace viewer, filtering, and cost-aggregation UI from scratch —
  exactly the work Langfuse already did, and not a skill a Salesforce FDE
  interview needs demonstrated from first principles.

## Consequences

Easier: `agent/loop.py`, `draft_response.py`, and `create_case.py` gain
tracing through one small, consistently-shaped interface; none of them
import `langfuse` directly, so swapping the backing SDK later touches one
file. The no-op contract means tracing can never become a prerequisite for
the agent working, in dev or in CI. Trace-level tags built in from the start
mean PR 3's eval set and PR 4's dashboard metrics don't need `agent/tracing.py`
redesigned to support them.

Harder: another third-party dependency in the demo's critical path when
configured (a Langfuse outage degrades to no-op automatically, but adds a
network round-trip per request when working). The cost constant is accurate
only as of its cited date — a model swap or Anthropic price change requires
a manual update, not something the code catches on its own.

**Data protection note (would differ in production).** Guest review text and
the agent's draft reply are sent to Langfuse as generation/span input and
output — this is required for tracing to be useful at all (seeing what the
model actually read and wrote is the point). In this project that data is
entirely synthetic (ADR-0001), so there's no real personal data leaving the
system. At a real customer, sending actual guest feedback — which can
include names, specific complaints, occasionally health or allergy
information — to a third-party observability vendor is a GDPR data
processing question, not a hypothetical one. In production this would need:
a Data Processing Agreement with Langfuse (or whichever vendor); a data
residency decision (an EU customer likely needs Langfuse's EU region or a
self-hosted deployment, not the default US cloud region this demo uses); and
masking or redaction of free-text fields — Langfuse's client accepts a
`mask` function for exactly this — before guest-authored text is attached to
a trace, keeping the review_id and structured fields (rating, severity,
outcome) for correlation while dropping the verbatim guest/agent text from
what leaves the system. None of this is built here; it's the explicit
"next step at a real customer," the same pattern ADR-0001 and ADR-0003 use
for their own production-vs-demo tradeoffs.
