# ADR-0003: Salesforce integration via REST API, not an Agentforce custom action

- **Status:** Accepted
- **Date:** 2026-07-24
- **Context:** Gästpuls v2 (FDE case)

## Context

The agent needs to create a Case in a real Salesforce Developer Edition org
when a review's severity warrants it. Salesforce offers two integration
paths for this: calling the standard REST API directly (`/sobjects/Case`),
or building an Agentforce custom action that Salesforce's own agent
platform invokes. This project's agent loop (`agent/loop.py`) is a
from-scratch tool-calling loop against the Anthropic SDK — the two
integration paths differ in where the "brain" lives: REST keeps it
entirely in `agent/`, an Agentforce action would move case-creation
decisions into Salesforce's own agent runtime.

## Decision

`agent/tools/create_case.py` calls the Salesforce REST API
(`/services/data/v61.0/sobjects/Case`) directly via `SalesforceClient`
(OAuth Client Credentials flow, see the M8 auth PR). Field mapping,
threshold logic, and deduplication all live in this repo's Python code.

## Alternatives considered

- **Agentforce custom action** — lets Salesforce's own agent platform call
  into the flow, which is compelling for a Salesforce-native production
  architecture. Rejected for now: it would require building and deploying
  an Agentforce action/topic inside the org, shifting orchestration logic
  into Salesforce metadata rather than the Python codebase this case study
  is meant to demonstrate. It also assumes a Salesforce-hosted invocation
  pattern that doesn't fit "one Python agent, tool-calling loop built from
  scratch."
- **Middleware/iPaaS (MuleSoft, etc.)** — real option at an actual
  customer, but pure overhead for a single-object write in a demo; out of
  scope per PROJECT_BRIEF's "avoid overengineering."

## Consequences

Easier: the whole review-to-Case path is inspectable and testable as plain
Python — every field mapping, threshold check, and dedup query is a
function in this repo, not an opaque platform config.

Harder: doesn't demonstrate the Salesforce-native extension points
(Agentforce actions, Flow, Apex triggers) a real production deployment
might use instead or in addition. Documented here as the explicit "next
step at a real customer."

**Known risk — severity/draft forwarding between tool calls.** `create_case`
takes `severity` and `draft_response` as arguments rather than
re-deriving them, because they're LLM output from a prior `draft_response`
call and can't be recomputed deterministically. In the general agent loop,
these values pass through the orchestrating model as tool-call arguments,
which means a hallucinated or malformed value could theoretically be
substituted in transit (a "transcription" error between tool calls).
Consequence is low: `create_case` re-validates and re-normalizes severity
itself (`CreateCaseError` on anything outside `low`/`medium`/`high`) and
re-applies the creation threshold independently — it does not trust the
caller's threshold judgment, only the severity value's shape. Worst case
is a wrongly-skipped or wrongly-created Case, both recoverable by a human
reviewing the Case queue, not a silent data-integrity failure.

Future hardening (not built here): have `create_case` accept an opaque
reference to the `draft_response` result (e.g. a short-lived ID it can
fetch by) instead of the raw values, so nothing LLM-generated is retyped
as tool-call arguments between steps.
