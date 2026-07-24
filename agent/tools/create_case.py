"""create_case tool: creates a Salesforce Case for a review whose severity
(from a prior draft_response call) is at or above the case-creation
threshold. Below the threshold is a valid, logged outcome, not an error.

Deduplicates by Subject before writing: the demo gets run against the same
seed data repeatedly, and a Subject built from restaurant + rating is a
stable, cheap key to check first via SOQL.
"""

import json
import logging
from urllib.parse import quote

from agent.salesforce_client import SalesforceClient
from agent.tools.get_context import fetch_context

logger = logging.getLogger(__name__)

SCHEMA = {
    "name": "create_case",
    "description": (
        "Create a Salesforce Case for a review whose severity is medium or "
        "high. Reviews below the threshold are skipped, not an error. "
        "Deduplicates: if a Case for the same restaurant/rating already "
        "exists, returns it instead of creating a duplicate."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "review_id": {"type": "string", "description": "UUID of the review."},
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Severity classification from draft_response.",
            },
            "draft_response": {"type": "string", "description": "Draft reply from draft_response."},
            "reasoning": {
                "type": "string",
                "description": "Severity reasoning from draft_response, included in the Case for context.",
            },
        },
        "required": ["review_id", "severity", "draft_response"],
    },
}

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}
CASE_CREATION_THRESHOLD = "medium"

CASE_SUBJECT_TEMPLATE = "[Gästpuls] {restaurant_name}: negative review ({rating}/5)"

CASE_DESCRIPTION_TEMPLATE = """Guest review (rating {rating}/5, source: {source}):
\"\"\"
{review_text}
\"\"\"

Draft reply sent to guest:
\"\"\"
{draft_response}
\"\"\"

Severity reasoning: {reasoning}

Gästpuls review_id: {review_id}
"""


class CreateCaseError(Exception):
    """Raised when the Salesforce API rejects the query or the create call."""


def _raise_for_salesforce_error(response, expected_status: int) -> None:
    if response.status_code != expected_status:
        raise CreateCaseError(f"Salesforce API error ({response.status_code}): {response.json()}")


def _find_existing_case(client: SalesforceClient, subject: str) -> str | None:
    escaped_subject = subject.replace("'", "\\'")
    soql = f"SELECT Id FROM Case WHERE Subject = '{escaped_subject}' LIMIT 1"
    response = client.request("GET", f"/query?q={quote(soql)}")
    _raise_for_salesforce_error(response, expected_status=200)

    records = response.json().get("records", [])
    return records[0]["Id"] if records else None


def run(
    review_id: str,
    severity: str,
    draft_response: str,
    reasoning: str = "",
    supabase_client=None,
    salesforce_client=None,
) -> str:
    severity = severity.strip().lower()
    if severity not in SEVERITY_ORDER:
        raise CreateCaseError(
            f"Unknown severity: {severity!r}. Expected one of {sorted(SEVERITY_ORDER)}."
        )

    if SEVERITY_ORDER[severity] < SEVERITY_ORDER[CASE_CREATION_THRESHOLD]:
        logger.info(
            "create_case skipped: review_id=%s severity=%s below threshold=%s",
            review_id,
            severity,
            CASE_CREATION_THRESHOLD,
        )
        return json.dumps(
            {
                "review_id": review_id,
                "status": "skipped",
                "reason": (
                    f"severity '{severity}' is below the case-creation "
                    f"threshold ('{CASE_CREATION_THRESHOLD}')"
                ),
            },
            ensure_ascii=False,
        )

    context = fetch_context(review_id, supabase_client=supabase_client)
    review = context["review"]
    restaurant = context["restaurant"]

    subject = CASE_SUBJECT_TEMPLATE.format(restaurant_name=restaurant["name"], rating=review["rating"])
    description = CASE_DESCRIPTION_TEMPLATE.format(
        rating=review["rating"],
        source=review["source"],
        review_text=review["text"],
        draft_response=draft_response,
        reasoning=reasoning or "(not provided)",
        review_id=review_id,
    )

    client = salesforce_client or SalesforceClient()

    existing_case_id = _find_existing_case(client, subject)
    if existing_case_id:
        logger.info(
            "create_case found existing case: review_id=%s case_id=%s", review_id, existing_case_id
        )
        return json.dumps(
            {"review_id": review_id, "status": "already_exists", "case_id": existing_case_id},
            ensure_ascii=False,
        )

    response = client.request(
        "POST",
        "/sobjects/Case",
        json={"Subject": subject, "Description": description, "Priority": severity.capitalize()},
    )
    _raise_for_salesforce_error(response, expected_status=201)
    case_id = response.json()["id"]
    case_url = f"{client.instance_url()}/lightning/r/Case/{case_id}/view"

    logger.info(
        "create_case created: review_id=%s severity=%s case_id=%s", review_id, severity, case_id
    )
    return json.dumps(
        {"review_id": review_id, "status": "created", "case_id": case_id, "case_url": case_url},
        ensure_ascii=False,
    )
