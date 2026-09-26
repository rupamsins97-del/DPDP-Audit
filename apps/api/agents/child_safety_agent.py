import logging
from typing import Any

from apps.api.agents.state import AuditContextState
from apps.api.tools.child_safety_scanner import audit_child_safety
from apps.api.tools.event_bus import get_event_bus

logger = logging.getLogger(__name__)


async def child_safety_agent_node(state: AuditContextState) -> dict[str, Any]:
    """Child Safety Agent: audits age-gating, DigiLocker VPC, and minor tracking suppression."""
    audit_id = state.get("audit_id", "unknown-audit")
    event_bus = get_event_bus()

    logger.info(f"[child_safety_agent] Evaluating minor tracking protection for audit {audit_id}")

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "child_safety_agent",
            "message": "Auditing age-gating mechanisms and Rule 10 Verifiable Parental Consent...",
        },
    )

    findings = audit_child_safety(
        has_age_gating=None,
    )

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "child_safety_agent",
            "message": f"Child safety audit complete. Generated {len(findings)} findings.",
        },
    )

    return {"findings": findings}
