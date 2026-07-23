"""Tool registry: each tool is a pure function plus a JSON schema, one file
per tool in agent/tools/. Tools are registered explicitly below rather than
auto-discovered, so the available set is always visible by reading this file.
"""

from dataclasses import dataclass
from typing import Callable

from agent.tools import draft_response, echo, get_context

_TOOL_MODULES = [echo, get_context, draft_response]


@dataclass(frozen=True)
class ToolSpec:
    schema: dict
    run: Callable[..., str]


TOOL_REGISTRY: dict[str, ToolSpec] = {
    module.SCHEMA["name"]: ToolSpec(schema=module.SCHEMA, run=module.run)
    for module in _TOOL_MODULES
}


def get_tool(name: str) -> ToolSpec | None:
    return TOOL_REGISTRY.get(name)


def list_schemas() -> list[dict]:
    return [tool.schema for tool in TOOL_REGISTRY.values()]
