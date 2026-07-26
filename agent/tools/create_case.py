"""create_case tool: creates a Salesforce Case for a review whose severity
(from a prior draft_response call) is at or above the case-creation
threshold. Below the threshold is a valid, logged outcome, not an error.

Deduplicates via upsert on the Gastpuls_Review_Id__c external ID field
(one PATCH to /sobjects/Case/Gastpuls_Review_Id__c/{review_id}), not a
SOQL lookup by Subject. Subject (restaurant + rating) collapsed distinct
reviews that happened to share a restaurant and rating into one Case;
review_id is the field that's actually unique per review. See ADR-0003
for why upsert-by-external-ID replaced the query-then-create pattern.
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
        "Deduplicates by upserting on the review's external ID: a second "
        "call for the same review_id updates the existing Case instead of "
        "creating a duplicate."
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

REVIEW_ID_FIELD = "Gastpuls_Review_Id__c"

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
"""


class CreateCaseError(Exception):
    """Raised when the Salesforce API rejects the upsert call."""


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
    )

    client = salesforce_client or SalesforceClient()

    # The external ID value goes in the URL only — Salesforce rejects an
    # upsert PATCH that also repeats the external ID field in the body
    # (INVALID_FIELD: "should not be specified in the sobject data").
    response = client.request(
        "PATCH",
        f"/sobjects/Case/{REVIEW_ID_FIELD}/{quote(review_id)}",
        json={
            "Subject": subject,
            "Description": description,
            "Priority": severity.capitalize(),
        },
    )

    if response.status_code == 201:
        case_id = response.json()["id"]
        case_url = f"{client.instance_url()}/lightning/r/Case/{case_id}/view"
        logger.info(
            "create_case created: review_id=%s severity=%s case_id=%s", review_id, severity, case_id
        )
        return json.dumps(
            {"review_id": review_id, "status": "created", "case_id": case_id, "case_url": case_url},
            ensure_ascii=False,
        )

    if response.status_code == 204:
        # Upsert-on-update returns no body, so no case_id/case_url is available
        # here without a second round trip — deliberately not fetched; see
        # ADR-0003.
        logger.info(
            "create_case updated existing case: review_id=%s severity=%s", review_id, severity
        )
        return json.dumps(
            {"review_id": review_id, "status": "updated"},
            ensure_ascii=False,
        )

    raise CreateCaseError(f"Salesforce API error ({response.status_code}): {response.json()}")
