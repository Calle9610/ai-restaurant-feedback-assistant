# ADR-0002: Tool-calling loop built from scratch instead of a framework

- **Status:** Accepted
- **Date:** 2026-07-23
- **Context:** Gästpuls v2 (FDE case)

## Context

The agent needs a loop that sends a prompt to Claude, lets the model choose
a tool, executes it, feeds the result back, and repeats until the model is
done. Frameworks like LangChain or LangGraph would give this for free, but
the case this project is built for explicitly asks for evidence of
understanding the mechanics of tool calling — what a "tool call" actually is
on the wire, how results get matched back to requests, what happens when a
tool fails or the model asks for something that doesn't exist. A framework
would hide exactly the parts that need to be visible and defensible in an
interview.

## Decision

`agent/loop.py` implements the loop directly against the Anthropic SDK's
`messages.create` API, with no agent framework in between. Tools are plain
functions with a JSON schema, registered explicitly in
`agent/tools/registry.py`.

## Alternatives considered

- **LangChain** — general-purpose but heavyweight for a single loop; its
  abstractions (agents, chains, callbacks) would obscure the exact
  tool-call/tool-result mechanics the case is meant to demonstrate.
- **LangGraph** — better suited to multi-step graphs with branching state
  than a single request/tool/response loop; adds a graph-execution model and
  its own state abstractions this project doesn't need.

## Consequences

Easier: every step of the loop (request, tool dispatch, error handling,
iteration cap) is a few lines of readable Python that can be walked through
line by line in an interview. No framework version churn or abstraction
leakage to debug.

Harder: no built-in retries, streaming helpers, or multi-agent orchestration
— if the project ever needed those, they'd be hand-rolled or the decision
revisited.

The model used by the loop (`AGENT_MODEL`, read in `agent/loop.py`) and the
Anthropic key it authenticates with (`AGENT_ANTHROPIC_API_KEY`, separate
from the webapp's own key) are both environment configuration, never
hardcoded. This makes the cost/quality tradeoff explicit and per-environment:
dev runs cheap on Haiku, demo/evals switch to a stronger model by setting a
variable, and the two Anthropic keys can be rotated and cost-attributed
independently between the webapp and the agent backend.
