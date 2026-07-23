"""CLI entry point: python -m agent.run --prompt "..." [--model ...]

Runs the tool-calling loop live against the real Anthropic API. Requires
AGENT_ANTHROPIC_API_KEY in .env.local; not run in CI.
"""

import argparse
import os

from dotenv import load_dotenv

from agent.loop import DEFAULT_MAX_ITERATIONS, run_loop

load_dotenv(".env.local")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Gästpuls agent tool-calling loop.")
    parser.add_argument("--prompt", required=True, help="Prompt to send to the agent.")
    parser.add_argument(
        "--model",
        default=None,
        help="Override AGENT_MODEL for this run.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help="Iteration cap before the loop raises MaxIterationsError.",
    )
    args = parser.parse_args()

    model = args.model or os.environ.get("AGENT_MODEL", "claude-haiku-4-5-20251001")
    print(f"[agent] model: {model}")

    result = run_loop(args.prompt, model=model, max_iterations=args.max_iterations)
    print(result.final_text)


if __name__ == "__main__":
    main()
