"""draft_response tool: classifies the operational severity of a guest
review and drafts a reply, via its own scoped Anthropic call.

Fetches its own context via get_context.fetch_context() rather than
requiring the caller to pass it in — the top-level agent loop can still
call get_context itself first to reason over, but draft_response doesn't
depend on that call happening. The extra fetch is cheap; the top-level
agent's visible reasoning over context before choosing this tool is not.
"""

import json

from agent.anthropic_client import get_client as get_anthropic_client
from agent.anthropic_client import get_model
from agent.tools.get_context import fetch_context

SCHEMA = {
    "name": "draft_response",
    "description": (
        "Classify the operational severity of a guest review (low/medium/"
        "high) and draft a Swedish-language reply. Fetches its own context "
        "for the given review_id."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "review_id": {"type": "string", "description": "UUID of the review."},
        },
        "required": ["review_id"],
    },
}

# Forces a schema-conformant response instead of parsing free text — the
# model must call this tool, so the "JSON parsing" is Anthropic's own
# tool-input validation, not regex over a text block.
RESPONSE_TOOL_SCHEMA = {
    "name": "submit_classification",
    "description": "Submit the severity classification and Swedish draft reply for this review.",
    "input_schema": {
        "type": "object",
        "properties": {
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Operational severity of the review.",
            },
            "reasoning": {
                "type": "string",
                "description": "1-2 sentences explaining the severity classification.",
            },
            "draft_response": {
                "type": "string",
                "description": "Guest-facing reply draft, in Swedish.",
            },
        },
        "required": ["severity", "reasoning", "draft_response"],
    },
}

VALID_SEVERITIES = {"low", "medium", "high"}

# Kept as one readable constant, filled in with a single .format() call, so
# it can be shown and discussed as-is rather than reconstructed from
# scattered string fragments.
CLASSIFICATION_PROMPT = """You are helping a restaurant group respond to a guest review.

Restaurant: {restaurant_name} ({restaurant_area})
Review rating: {rating}/5 (source: {source})
Review text:
\"\"\"
{review_text}
\"\"\"
{analysis_block}
Your task:
1. Classify the operational severity of this review as one of: low, medium, high.
   - high: serious complaints requiring management follow-up (health/safety,
     discrimination, repeated failures, guest threatening to leave/never return).
   - medium: a real problem worth addressing, but not urgent (slow service,
     one-off food quality issue).
   - low: minor gripes, mixed feedback, or mostly positive reviews with small notes.
2. Draft a reply to the guest.
   - Write the reply in SWEDISH. The review is in Swedish and the reply is
     published to a Swedish guest.
   - Tone: professional and empathetic. Address the SPECIFIC issue the guest
     raised — do not use generic filler like "vi beklagar det inträffade"
     without saying what "det" was.
   - Keep it short: 2-4 sentences.

Call submit_classification with your severity, a short reasoning, and the draft reply.
"""


class DraftResponseError(Exception):
    """Raised when the model's structured output doesn't hold up to validation."""


def _build_prompt(context: dict) -> str:
    review = context["review"]
    restaurant = context["restaurant"]
    analysis = context.get("analysis")
    analysis_block = (
        f"\nExisting categorization: sentiment={analysis['sentiment']}, "
        f"category={analysis['category']}, summary=\"{analysis['summary']}\"\n"
        if analysis
        else ""
    )
    return CLASSIFICATION_PROMPT.format(
        restaurant_name=restaurant["name"],
        restaurant_area=restaurant["area"],
        rating=review["rating"],
        source=review["source"],
        review_text=review["text"],
        analysis_block=analysis_block,
    )


def _validate_and_normalize(classification: dict) -> dict:
    missing = [key for key in ("severity", "reasoning", "draft_response") if key not in classification]
    if missing:
        raise DraftResponseError(f"Model output missing required field(s): {missing}")

    severity = classification["severity"].strip().lower()
    if severity not in VALID_SEVERITIES:
        raise DraftResponseError(
            f"Model returned an invalid severity: {classification['severity']!r}. "
            f"Expected one of {sorted(VALID_SEVERITIES)}."
        )

    return {
        "severity": severity,
        "reasoning": classification["reasoning"],
        "draft_response": classification["draft_response"],
    }


def run(
    review_id: str,
    supabase_client=None,
    anthropic_client=None,
    model: str | None = None,
) -> str:
    context = fetch_context(review_id, supabase_client=supabase_client)
    prompt = _build_prompt(context)

    client = anthropic_client or get_anthropic_client()
    response = client.messages.create(
        model=get_model(model),
        max_tokens=1024,
        tools=[RESPONSE_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "submit_classification"},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use = next(block for block in response.content if block.type == "tool_use")
    classification = _validate_and_normalize(tool_use.input)

    result = {"review_id": review_id, **classification}
    return json.dumps(result, ensure_ascii=False)
