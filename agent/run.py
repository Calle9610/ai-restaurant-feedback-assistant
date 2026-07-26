"""CLI entry point.

    python -m agent.run --prompt "..." [--model ...]
    python -m agent.run --review-id <uuid> [--model ...] [--session-id ...]

--prompt runs the general tool-calling loop live against the real Anthropic
API. --review-id classifies severity, drafts a reply, and (if severity is
at or above the case-creation threshold) creates a Salesforce Case —
calling draft_response and create_case directly, skipping the general loop.
Both require AGENT_ANTHROPIC_API_KEY in .env.local; --review-id also
requires the SF_* Salesforce credentials. Neither runs in CI.

Both modes are traced (agent/tracing.py, docs/adr/ADR-0004-observability.md)
— a no-op unless LANGFUSE_PUBLIC_KEY/LANGFUSE_SECRET_KEY are set. --review-id
opens one outer trace per invocation; draft_response and create_case each
open their own nested trace, which Langfuse's ambient OpenTelemetry context
attaches as child spans of this one rather than separate traces. --session-id
groups multiple --review-id runs under one Langfuse session (e.g. for an
eval batch in M9's eval-set work) without needing any interface change.
"""

import argparse
import json
import logging

from dotenv import load_dotenv

from agent.anthropic_client import get_model
from agent.loop import DEFAULT_MAX_ITERATIONS, run_loop
from agent.tools import create_case, draft_response
from agent.tracing import get_tracer

load_dotenv(".env.local")


def _run_review_id(review_id: str, model: str, session_id: str | None) -> None:
    tracer = get_tracer()
    with tracer.trace(
        "agent.review_id_flow",
        tags=["review-id-mode"],
        metadata={"review_id": review_id, "model": model},
        session_id=session_id,
    ):
        result = json.loads(draft_response.run(review_id, model=model, tracer=tracer, session_id=session_id))
        print(f"severity: {result['severity']}")
        print(f"reasoning: {result['reasoning']}")
        print(f"draft response:\n{result['draft_response']}")

        case_result = json.loads(
            create_case.run(
                review_id,
                severity=result["severity"],
                draft_response=result["draft_response"],
                reasoning=result["reasoning"],
                tracer=tracer,
                session_id=session_id,
            )
        )
        if case_result["status"] == "created":
            print(f"case: created {case_result['case_id']} -> {case_result['case_url']}")
        elif case_result["status"] == "updated":
            print("case: updated existing case")
        else:
            print(f"case: skipped — {case_result['reason']}")

    tracer.flush()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Run the Gästpuls agent tool-calling loop.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prompt", help="Prompt to send to the general tool-calling loop.")
    mode.add_argument(
        "--review-id",
        help="Review UUID: classify severity, draft a reply, and create a Case if warranted.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override AGENT_MODEL for this run.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help="Iteration cap before the loop raises MaxIterationsError (--prompt mode only).",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help=(
            "Langfuse session ID to group this run's trace with others (e.g. an "
            "eval batch). --review-id mode only; no-op if tracing isn't configured."
        ),
    )
    args = parser.parse_args()

    model = get_model(args.model)
    print(f"[agent] model: {model}")

    if args.review_id:
        _run_review_id(args.review_id, model, args.session_id)
        return

    result = run_loop(args.prompt, model=model, max_iterations=args.max_iterations)
    print(result.final_text)
    get_tracer().flush()


if __name__ == "__main__":
    main()
