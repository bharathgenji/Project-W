"""AI-powered lead enrichment using Gemini (gemma-3-27b-it free tier).

Parses permit/bid descriptions into structured data:
- Project type: new_build / renovation / repair / addition / compliance
- Owner type: residential / small_commercial / large_commercial / institutional
- Estimated sq footage, unit count, key materials
- Urgency + complexity signals

Free tier limits: gemma-3-27b-it — 30 RPM, 14,400 RPD
We target ~28 RPM (2.15s between calls) with a per-run cap.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

from shared.config import get_settings

logger = logging.getLogger(__name__)

# ── Prompt — double-brace {{ }} escapes literal braces in .format() ──────────
_PROMPT = """\
Construction permit. Return ONLY JSON, no markdown:
{{"project_type":"new_build|renovation|repair|addition|compliance","owner_type":"residential|small_commercial|large_commercial|institutional","sqft":null,"units":null,"key_materials":[],"urgency":"high|medium|low","complexity":"simple|moderate|complex"}}

Fill for: {description}"""

# ── Module-level state ────────────────────────────────────────────────────────
_enriched_this_run: int = 0
_last_call_ts: float = 0.0
_MIN_INTERVAL = 16.0          # seconds between calls → ~3.5 RPM, ~1200 TPM (under 1500 TPM limit)
_QUOTA_ERRORS = 0
_MAX_QUOTA_ERRORS = 3         # give up after 3 consecutive 429s


async def _rate_limited_pause() -> None:
    """Enforce minimum interval between API calls to stay under 30 RPM."""
    global _last_call_ts
    elapsed = time.monotonic() - _last_call_ts
    if elapsed < _MIN_INTERVAL:
        await asyncio.sleep(_MIN_INTERVAL - elapsed)
    _last_call_ts = time.monotonic()


def _extract_json(raw: str) -> dict:
    """Extract first JSON object from a string, stripping any markdown fences."""
    # Strip ```json ... ``` fences
    text = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text.strip(), flags=re.MULTILINE)
    # Find first { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in: {text[:100]}")
    return json.loads(match.group())


async def enrich_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """
    Call Gemini to extract structured data from a lead's description.
    Returns updated lead dict with 'ai' field added (or original on error).
    """
    global _enriched_this_run, _QUOTA_ERRORS

    settings = get_settings()
    if not settings.has_ai_enrichment:
        return lead

    # Per-run cap — don't exhaust free tier quota on a single large batch
    if _enriched_this_run >= settings.ai_enrichment_max_per_run:
        return lead

    # Stop trying after repeated quota errors
    if _QUOTA_ERRORS >= _MAX_QUOTA_ERRORS:
        return lead

    description = (lead.get("title", "") + " " + lead.get("work_description", "")).strip()
    if len(description) < 20:
        return lead

    try:
        await _rate_limited_pause()

        if settings.gemini_api_key:
            result = await _call_gemini(settings.gemini_api_key, settings.ai_enrichment_model, description)
        elif settings.anthropic_api_key:
            result = await _call_anthropic(settings.anthropic_api_key, description)
        else:
            return lead

        lead["ai"] = result
        _enriched_this_run += 1
        _QUOTA_ERRORS = 0  # reset on success
        logger.info(f"enriched lead={lead.get('id','?')[:8]} type={result.get('project_type')} [{_enriched_this_run}/{settings.ai_enrichment_max_per_run}]")

    except json.JSONDecodeError as exc:
        logger.warning(f"ai_enrichment_parse_error: {exc}")
    except Exception as exc:
        err = str(exc)
        if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
            _QUOTA_ERRORS += 1
            logger.warning(f"ai_enrichment_quota ({_QUOTA_ERRORS}/{_MAX_QUOTA_ERRORS}): backing off")
            await asyncio.sleep(60)  # back off 60s on quota hit
        elif "credit" in err.lower() or "402" in err:
            _QUOTA_ERRORS = _MAX_QUOTA_ERRORS  # disable immediately
            logger.warning("ai_enrichment_disabled: no API credits")
        else:
            logger.warning(f"ai_enrichment_error: {err[:120]}")

    return lead


async def _call_gemini(api_key: str, model: str, description: str) -> dict:
    """Call Gemini via google.genai SDK (runs sync client in thread executor)."""
    import asyncio
    from google import genai  # type: ignore

    prompt = _PROMPT.format(description=description[:800])

    def _sync_call() -> str:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model=model, contents=prompt)
        return resp.text

    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _sync_call)
    return _extract_json(raw)


async def _call_anthropic(api_key: str, description: str) -> dict:
    """Fallback: Anthropic Claude (if credits available)."""
    import anthropic  # type: ignore

    prompt = _PROMPT.format(description=description[:800])

    def _sync_call() -> str:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _sync_call)
    return _extract_json(raw)


def reset_run_counter() -> None:
    """Call at the start of each ingestion run to reset the per-run cap."""
    global _enriched_this_run, _QUOTA_ERRORS
    _enriched_this_run = 0
    _QUOTA_ERRORS = 0
