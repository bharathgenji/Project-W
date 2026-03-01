"""AI-powered lead enrichment using Claude.

Parses messy permit/bid descriptions into structured data:
- Project type classification (new_build / renovation / repair / addition)
- Owner type (residential / small_commercial / large_commercial / institutional)
- Estimated square footage, unit count
- Key materials mentioned
- Urgency signals

Cost: ~$0.003/lead with claude-haiku-4-5, ~$0.015 with claude-sonnet-4-6
"""
from __future__ import annotations

import json
import logging
from typing import Any

from shared.config import get_settings

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
Extract structured data from this construction permit or bid description.
Return ONLY valid JSON, no explanation.

Schema:
{
  "project_type": "new_build" | "renovation" | "repair" | "addition" | "compliance",
  "owner_type": "residential" | "small_commercial" | "large_commercial" | "institutional",
  "sqft": <number or null>,
  "units": <number or null>,
  "key_materials": [<list of specific materials, max 5>],
  "urgency": "high" | "medium" | "low",
  "complexity": "simple" | "moderate" | "complex"
}

Description: {description}

Return ONLY the JSON object."""


async def enrich_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """
    Call Claude to extract structured data from a lead's description.
    Returns updated lead dict with 'ai' field added.
    Non-blocking — logs and returns original on any error.
    """
    settings = get_settings()
    if not settings.has_ai_enrichment:
        return lead

    description = lead.get("title", "") + " " + lead.get("work_description", "")
    description = description.strip()
    if len(description) < 20:
        return lead

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        response = client.messages.create(
            model=settings.ai_enrichment_model,
            max_tokens=350,
            messages=[{
                "role": "user",
                "content": _EXTRACTION_PROMPT.format(description=description[:800]),
            }],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        ai_data = json.loads(raw.strip())
        lead["ai"] = ai_data
        logger.info("ai_enrichment_ok", lead_id=lead.get("id"), project_type=ai_data.get("project_type"))

    except json.JSONDecodeError as exc:
        logger.warning("ai_enrichment_parse_error", error=str(exc))
    except Exception as exc:
        logger.warning("ai_enrichment_failed", error=str(exc))

    return lead
