"""CLI entry point.

    python -m agent.run --prompt "..." [--model ...]
    python -m agent.run --review-id <uuid> [--model ...]

--prompt runs the general tool-calling loop live against the real Anthropic
API. --review-id calls the draft_response tool directly for a single review,
skipping the general loop. Both require AGENT_ANTHROPIC_API_KEY in
.env.local; neither runs in CI.
"""

import argparse
import json

from dotenv import load_dotenv

from agent.anthropic_client import get_model
from agent.loop import DEFAULT_MAX_ITERATIONS, run_loop
from agent.tools import draft_response

load_dotenv(".env.local")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Gästpuls agent tool-calling loop.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prompt", help="Prompt to send to the general tool-calling loop.")
    mode.add_argument(
        "--review-id",
        help="Review UUID: classify severity and draft a reply directly, skipping the general loop.",
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
        result = json.loads(draft_response.run(args.review_id, model=model))
        print(f"severity: {result['severity']}")
        print(f"reasoning: {result['reasoning']}")
        print(f"draft response:\n{result['draft_response']}")
        return

    result = run_loop(args.prompt, model=model, max_iterations=args.max_iterations)
    print(result.final_text)


if __name__ == "__main__":
    main()
