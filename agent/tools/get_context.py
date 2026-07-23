"""get_context tool: fetches structured context for a single review from
Supabase — the review itself, its restaurant, and any existing sentiment/
category analysis from the v1 categorization pipeline (review_analysis).
"""

import json

from agent.db import get_client as get_supabase_client

SCHEMA = {
    "name": "get_context",
    "description": (
        "Fetch structured context for a single guest review: the review "
        "itself, its restaurant, and any existing sentiment/category "
        "analysis. Call this before judging severity or drafting a reply."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "review_id": {"type": "string", "description": "UUID of the review."},
        },
        "required": ["review_id"],
    },
}


def fetch_context(review_id: str, supabase_client=None) -> dict:
    client = supabase_client or get_supabase_client()
    response = (
        client.table("reviews")
        .select(
            "id, rating, text, source, created_at, "
            "restaurants(name, area), "
            "review_analysis(sentiment, category, summary, suggested_action)"
        )
        .eq("id", review_id)
        .single()
        .execute()
    )
    row = response.data
    restaurant = row.get("restaurants") or {}

    # review_analysis is a one-to-one relation, but PostgREST embeds can come
    # back as either a single object or a single-item list depending on FK
    # direction — normalize both shapes.
    analysis_raw = row.get("review_analysis")
    if isinstance(analysis_raw, list):
        analysis = analysis_raw[0] if analysis_raw else None
    else:
        analysis = analysis_raw

    return {
        "review": {
            "id": row["id"],
            "rating": row["rating"],
            "text": row["text"],
            "source": row["source"],
            "created_at": row["created_at"],
        },
        "restaurant": {
            "name": restaurant.get("name"),
            "area": restaurant.get("area"),
        },
        "analysis": (
            {
                "sentiment": analysis["sentiment"],
                "category": analysis["category"],
                "summary": analysis["summary"],
                "suggested_action": analysis["suggested_action"],
            }
            if analysis
            else None
        ),
    }


def run(review_id: str, supabase_client=None) -> str:
    context = fetch_context(review_id, supabase_client=supabase_client)
    return json.dumps(context, ensure_ascii=False)
