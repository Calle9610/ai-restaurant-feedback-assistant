"""CLI entry point.

    python -m agent.run --prompt "..." [--model ...]
    python -m agent.run --review-id <uuid> [--model ...]

--prompt runs the general tool-calling loop live against the real Anthropic
API. --review-id classifies severity, drafts a reply, and (if severity is
at or above the case-creation threshold) creates a Salesforce Case —
calling draft_response and create_case directly, skipping the general loop.
Both require AGENT_ANTHROPIC_API_KEY in .env.local; --review-id also
requires the SF_* Salesforce credentials. Neither runs in CI.
"""

import argparse
import json
import logging

from dotenv import load_dotenv

from agent.anthropic_client import get_model
from agent.loop import DEFAULT_MAX_ITERATIONS, run_loop
from agent.tools import create_case, draft_response

load_dotenv(".env.local")


def _run_review_id(review_id: str, model: str) -> None:
    result = json.loads(draft_response.run(review_id, model=model))
    print(f"severity: {result['severity']}")
    print(f"reasoning: {result['reasoning']}")
    print(f"draft response:\n{result['draft_response']}")

    case_result = json.loads(
        create_case.run(
            review_id,
            severity=result["severity"],
            draft_response=result["draft_response"],
            reasoning=result["reasoning"],
        )
    )
    if case_result["status"] == "created":
        print(f"case: created {case_result['case_id']} -> {case_result['case_url']}")
    elif case_result["status"] == "already_exists":
        print(f"case: already exists ({case_result['case_id']})")
    else:
        print(f"case: skipped — {case_result['reason']}")


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
    args = parser.parse_args()

    model = get_model(args.model)
    print(f"[agent] model: {model}")

    if args.review_id:
        _run_review_id(args.review_id, model)
        return

    result = run_loop(args.prompt, model=model, max_iterations=args.max_iterations)
    print(result.final_text)


if __name__ == "__main__":
    main()
