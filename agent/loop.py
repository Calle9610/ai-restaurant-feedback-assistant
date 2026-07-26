"""Tool-calling loop: prompt -> model picks a tool -> execute -> result fed
back -> repeat until the model is done or the iteration cap is hit.

Built from scratch against the Anthropic SDK (no agent framework) — see
docs/adr/ADR-0002-tool-loop-from-scratch.md for why. Wrapped in Langfuse
tracing (docs/adr/ADR-0004-observability.md): a no-op tracer by default when
Langfuse isn't configured, so the loop's behavior never depends on tracing
being enabled — see agent/tracing.py.
"""

from dataclasses import dataclass

from anthropic import Anthropic

from agent.anthropic_client import get_client
from agent.tools.registry import get_tool, list_schemas
from agent.tracing import Tracer, TraceHandle, get_tracer, usage_and_cost_fields

DEFAULT_MAX_ITERATIONS = 10


class MaxIterationsError(Exception):
    """Raised when the loop hits its iteration cap without the model finishing.

    Carries the full message history as `.messages` — when the loop doesn't
    converge, the transcript is what you need to see why.
    """

    def __init__(self, max_iterations: int, messages: list[dict]):
        super().__init__(
            f"Agent loop hit the max-iterations cap ({max_iterations}) "
            "without producing a final answer."
        )
        self.max_iterations = max_iterations
        self.messages = messages


@dataclass
class LoopResult:
    final_text: str
    messages: list[dict]
    model: str


def _execute_tool_call(block, trace: TraceHandle) -> dict:
    tool = get_tool(block.name)
    if tool is None:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Unknown tool: {block.name!r}. No such tool is registered.",
            "is_error": True,
        }
    with trace.span(f"tool:{block.name}", input=block.input) as span:
        try:
            result = tool.run(**block.input)
        except Exception as exc:  # reported back to the model, not swallowed
            span.update(output=f"{type(exc).__name__}: {exc}", metadata={"error": "true"})
            return {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"{type(exc).__name__}: {exc}",
                "is_error": True,
            }
        span.update(output=result)
    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": result,
    }


def run_loop(
    prompt: str,
    model: str,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    client: Anthropic | None = None,
    tracer: Tracer | None = None,
) -> LoopResult:
    client = client or get_client()
    tracer = tracer or get_tracer()
    messages: list[dict] = [{"role": "user", "content": prompt}]

    with tracer.trace("agent.run_loop", tags=["prompt-mode"], metadata={"model": model}) as trace:
        for _ in range(max_iterations):
            with trace.generation("anthropic.messages.create", model=model, input=messages) as gen:
                response = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    tools=list_schemas(),
                    messages=messages,
                )
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "input_tokens", 0) or 0
                output_tokens = getattr(usage, "output_tokens", 0) or 0
                gen.update(
                    output=[
                        block.text for block in response.content if getattr(block, "type", None) == "text"
                    ],
                    **usage_and_cost_fields(model, input_tokens, output_tokens),
                )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                final_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                trace.set_outcome(tags=[f"stop:{response.stop_reason}"])
                return LoopResult(final_text=final_text, messages=messages, model=model)

            # The API can request several tool calls in one response; each result
            # must be matched back to its own tool_use_id.
            tool_results = [
                _execute_tool_call(block, trace)
                for block in response.content
                if block.type == "tool_use"
            ]
            messages.append({"role": "user", "content": tool_results})

        trace.set_outcome(tags=["max_iterations"])
        raise MaxIterationsError(max_iterations, messages)
