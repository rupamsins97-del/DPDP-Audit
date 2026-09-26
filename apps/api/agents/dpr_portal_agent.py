import logging
from typing import Any

from apps.api.agents.state import AuditContextState
from apps.api.tools.dpr_portal_scanner import audit_dpr_portal
from apps.api.tools.event_bus import get_event_bus

logger = logging.getLogger(__name__)


async def dpr_portal_agent_node(state: AuditContextState) -> dict[str, Any]:
    """DPR Portal Agent: audits DPR resolution SLA timers, nomination, and Consent Managers."""
    audit_id = state.get("audit_id", "unknown-audit")
    event_bus = get_event_bus()

    logger.info(f"[dpr_portal_agent] Evaluating DPR SLA & grievance readiness for {audit_id}")

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "dpr_portal_agent",
            "message": "Auditing grievance resolution SLA timers against Rule 14(3) (<=90 days)...",
        },
    )

    findings = audit_dpr_portal(
        grievance_sla_days=None,
    )

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "dpr_portal_agent",
            "message": f"DPR portal audit complete. Generated {len(findings)} findings.",
        },
    )

    return {"findings": findings}
