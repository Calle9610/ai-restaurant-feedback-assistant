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

## Amendment (2026-07-26): dedup via external ID upsert, not SOQL-by-Subject

**Original decision** deduplicated by querying `Case` for a matching
`Subject` (built from `restaurant + rating`) before deciding whether to
POST a new one. This shipped a bug: `Subject` is not a unique key over
reviews. Two distinct reviews for the same restaurant with the same
rating produce the same Subject, so the second one silently collapsed
into `already_exists` against the first review's Case — a real review
never got its own Case, with no error raised.

**New decision:** a Salesforce custom field, `Gastpuls_Review_Id__c`
(Text(50), External ID, Unique), added to `Case`, holding the actual
unique key: the review's UUID. `create_case` now does a single upsert —
`PATCH /sobjects/Case/Gastpuls_Review_Id__c/{review_id}` — instead of a
SOQL query followed by a conditional POST. Salesforce returns `201` when
the upsert created a new record and `204` when it updated an existing
one; these map to `{"status": "created"}` and `{"status": "updated"}`
respectively.

Why this is the right pattern, not just a bug patch:

- **Correct key.** The dedup key is now the same identifier the rest of
  the system already treats as unique (`review_id`), not a derived,
  collidable proxy.
- **Idempotent by construction.** Calling `create_case` twice for the
  same `review_id` is safe and cheap — it converges on one Case either
  way, which matters for a demo re-run against the same seed data and for
  any future retry-on-failure logic.
- **One API call instead of two.** The old path always cost a SOQL query
  plus, on the non-duplicate branch, a POST. The upsert is a single
  round trip regardless of outcome.
- **No race condition.** Query-then-create has a check-then-act gap: two
  concurrent calls for the same review could both see "no existing case"
  and both POST, producing a duplicate. Salesforce enforces the upsert's
  external-ID uniqueness at the database layer, so the same race
  resolves to one record no matter how the calls interleave — this
  repo's current call pattern is sequential and wouldn't hit that race in
  practice, but the upsert removes the class of bug rather than relying
  on call-pattern discipline to avoid it.

The `Gästpuls review_id: {review_id}` line was removed from the Case
`Description` template as part of this change — it was there as a manual
cross-reference back to Supabase, which is now redundant with a proper
(and queryable, reportable) field on the Case object itself.

One tradeoff accepted: Salesforce's upsert returns no body on `204`
(update), so `create_case` cannot return a `case_id`/`case_url` for the
`updated` outcome without a second round trip. Not fetched here, to keep
the upsert a single call — the trade favors staying idempotent-in-one-call
over always returning a fully-populated result on every outcome.

**Correction (same day):** the first version of this fix also set
`Gastpuls_Review_Id__c` in the PATCH body alongside putting it in the URL.
Salesforce's real API rejects that combination
(`INVALID_FIELD: "should not be specified in the sobject data"`) — an
upsert's external ID value is supplied by the URL segment only. Caught by
running the demo batch against the live org post-merge, before any Case
was written (the org was cleared and the run failed cleanly on all 5
medium-severity calls, no partial writes). Fixed by dropping the field
from the request body; it remains the URL's job to identify the record.
