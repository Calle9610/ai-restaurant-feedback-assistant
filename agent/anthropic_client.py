"""Shared Anthropic client construction for the agent backend.

Centralizes the AGENT_ANTHROPIC_API_KEY / AGENT_MODEL env contract so
agent/loop.py and any tool that makes its own LLM call (e.g. draft_response)
build the client and resolve the model the same way.
"""

import os

from anthropic import Anthropic

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def get_client() -> Anthropic:
    return Anthropic(api_key=os.environ["AGENT_ANTHROPIC_API_KEY"])


def get_model(override: str | None = None) -> str:
    return override or os.environ.get("AGENT_MODEL", DEFAULT_MODEL)
