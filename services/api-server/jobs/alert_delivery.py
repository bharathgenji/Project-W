"""Email alert delivery using Resend.

Fetches all active alerts, finds new matching leads, sends digest emails.
Called by: POST /api/internal/run-alert-delivery (Cloud Scheduler or cron)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from google.cloud.firestore_v1.base_query import FieldFilter

from shared.config import get_settings

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #111827; margin: 0; padding: 0; background: #f9fafb; }}
  .container {{ max-width: 600px; margin: 32px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .header {{ background: #1d4ed8; padding: 28px 32px; }}
  .header h1 {{ color: white; margin: 0; font-size: 22px; font-weight: 700; }}
  .header p {{ color: #bfdbfe; margin: 4px 0 0; font-size: 14px; }}
  .body {{ padding: 28px 32px; }}
  .lead {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 16px; }}
  .lead-title {{ font-size: 15px; font-weight: 600; color: #111827; margin-bottom: 8px; }}
  .lead-meta {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }}
  .badge {{ background: #eff6ff; color: #1d4ed8; border-radius: 6px; padding: 3px 10px; font-size: 12px; font-weight: 500; }}
  .badge.green {{ background: #ecfdf5; color: #065f46; }}
  .lead-value {{ font-size: 20px; font-weight: 700; color: #111827; }}
  .lead-addr {{ font-size: 13px; color: #6b7280; margin-top: 4px; }}
  .cta {{ display: inline-block; margin-top: 14px; background: #1d4ed8; color: white; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 600; }}
  .footer {{ background: #f9fafb; border-top: 1px solid #e5e7eb; padding: 20px 32px; font-size: 12px; color: #9ca3af; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🏗️ BuildScope — {count} New Lead{plural}</h1>
    <p>Matching your alert for {filter_desc}</p>
  </div>
  <div class="body">
    {leads_html}
    <p style="color:#6b7280;font-size:13px;margin-top:24px;">
      You're receiving this because you set up an alert on BuildScope.<br>
      <a href="https://buildscope.app/alerts" style="color:#1d4ed8;">Manage your alerts</a>
    </p>
  </div>
  <div class="footer">
    BuildScope · Construction Lead Intelligence<br>
    <a href="https://buildscope.app/alerts" style="color:#6b7280;">Unsubscribe</a>
  </div>
</div>
</body>
</html>
"""

LEAD_HTML = """\
<div class="lead">
  <div class="lead-title">{title}</div>
  <div class="lead-meta">
    <span class="badge">{trade}</span>
    <span class="badge">{lead_type}</span>
    <span class="badge green">Score {score}</span>
  </div>
  <div class="lead-value">{value}</div>
  <div class="lead-addr">📍 {addr}</div>
  {contact_html}
  <a href="https://buildscope.app/leads/{lead_id}" class="cta">View Full Lead →</a>
</div>
"""


def _format_value(v: Any) -> str:
    if not v:
        return "Value TBD"
    v = float(v)
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:,.0f}"


def _matches_alert(lead: dict, alert: dict) -> bool:
    if alert.get("trade") and alert["trade"] != lead.get("trade"):
        return False
    if alert.get("state") and alert["state"].upper() not in (lead.get("addr") or "").upper():
        return False
    if alert.get("city") and alert["city"].lower() not in (lead.get("addr") or "").lower():
        return False
    if alert.get("min_value") and (lead.get("value") or 0) < alert["min_value"]:
        return False
    if alert.get("max_value") and (lead.get("value") or 0) > alert["max_value"]:
        return False
    return True


def _build_filter_desc(alert: dict) -> str:
    parts = []
    if alert.get("trade"):
        parts.append(alert["trade"])
    if alert.get("state"):
        parts.append(alert["state"])
    if alert.get("city"):
        parts.append(alert["city"])
    return " · ".join(parts) if parts else "all construction leads"


async def send_alert_email(to_email: str, leads: list[dict], alert: dict, api_key: str, from_email: str) -> bool:
    """Send a digest email with matching leads using Resend API."""
    if not leads:
        return True

    leads_html_parts = []
    for lead in leads[:5]:  # max 5 leads per email
        owner = lead.get("owner") or {}
        contact_html = ""
        if owner.get("p"):
            contact_html = f'<p style="font-size:13px;color:#374151;margin:8px 0 0;">📞 {owner["p"]}</p>'
        elif owner.get("e"):
            contact_html = f'<p style="font-size:13px;color:#374151;margin:8px 0 0;">✉️ {owner["e"]}</p>'

        leads_html_parts.append(LEAD_HTML.format(
            title=lead.get("title", "")[:100],
            trade=lead.get("trade", ""),
            lead_type=(lead.get("type") or "permit").title(),
            score=lead.get("score", 0),
            value=_format_value(lead.get("value")),
            addr=lead.get("addr", ""),
            contact_html=contact_html,
            lead_id=lead.get("id", ""),
        ))

    count = len(leads)
    html = HTML_TEMPLATE.format(
        count=count,
        plural="s" if count != 1 else "",
        filter_desc=_build_filter_desc(alert),
        leads_html="".join(leads_html_parts),
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"BuildScope <{from_email}>",
                    "to": [to_email],
                    "subject": f"🏗️ {count} new lead{'s' if count != 1 else ''} match your BuildScope alert",
                    "html": html,
                },
            )
        if resp.status_code in (200, 201):
            logger.info("alert_email_sent", to=to_email, leads=count)
            return True
        else:
            logger.warning("alert_email_failed", to=to_email, status=resp.status_code, body=resp.text[:200])
            return False
    except Exception as exc:
        logger.error("alert_email_error", to=to_email, error=str(exc))
        return False


async def run_alert_delivery(db: Any) -> dict:
    """Main job: check all active alerts, send digest emails for new leads."""
    settings = get_settings()
    if not settings.has_email:
        return {"status": "skipped", "reason": "RESEND_API_KEY not configured"}

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(tzinfo=None).isoformat()

    # Get all active alerts
    alert_docs = db.alerts().where(filter=FieldFilter("active", "==", True)).limit(1000).stream()
    alerts = [{**doc.to_dict(), "id": doc.id} for doc in alert_docs]

    if not alerts:
        return {"status": "ok", "emails_sent": 0, "reason": "no active alerts"}

    # Get recently added leads (last 24h)
    lead_docs = db.leads().limit(500).stream()
    recent_leads = []
    for doc in lead_docs:
        data = {**doc.to_dict(), "id": doc.id}
        posted = data.get("posted") or ""
        if posted >= cutoff:
            recent_leads.append(data)

    if not recent_leads:
        return {"status": "ok", "emails_sent": 0, "reason": "no new leads in last 24h"}

    # Group by email
    email_to_leads: dict[str, list[dict]] = {}
    email_to_alert: dict[str, dict] = {}
    for alert in alerts:
        email = alert.get("email", "")
        if not email:
            continue
        matches = [l for l in recent_leads if _matches_alert(l, alert)]
        if matches:
            email_to_leads.setdefault(email, []).extend(matches)
            email_to_alert[email] = alert  # use last alert for filter desc

    # Remove duplicates per email
    for email in email_to_leads:
        seen = set()
        deduped = []
        for lead in email_to_leads[email]:
            if lead["id"] not in seen:
                seen.add(lead["id"])
                deduped.append(lead)
        email_to_leads[email] = sorted(deduped, key=lambda x: x.get("score", 0), reverse=True)

    # Send emails
    sent = 0
    for email, leads in email_to_leads.items():
        ok = await send_alert_email(
            email, leads, email_to_alert[email],
            settings.resend_api_key, settings.email_from
        )
        if ok:
            sent += 1

    return {"status": "ok", "emails_sent": sent, "alerts_checked": len(alerts), "new_leads": len(recent_leads)}
