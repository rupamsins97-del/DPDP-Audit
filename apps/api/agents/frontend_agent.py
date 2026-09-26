import logging
from typing import Any

from apps.api.agents.state import AuditContextState
from apps.api.tools.browser_scanner import audit_web_frontend
from apps.api.tools.event_bus import get_event_bus

logger = logging.getLogger(__name__)


async def frontend_agent_node(state: AuditContextState) -> dict[str, Any]:
    """Frontend Agent: executes Stagehand/CDP browser audit and AXTree verification."""
    audit_id = state.get("audit_id", "unknown-audit")
    target_url = state.get("target_url")
    governance_promises_list = state.get("governance_promises", [])
    event_bus = get_event_bus()

    # Aggregate governance promises dictionary
    gov_promises: dict[str, Any] = {}
    if governance_promises_list:
        if isinstance(governance_promises_list, list):
            for item in governance_promises_list:
                if isinstance(item, dict):
                    gov_promises.update(item)
        elif isinstance(governance_promises_list, dict):
            gov_promises = governance_promises_list

    logger.info(
        f"[frontend_agent] Starting browser inspection for {target_url} (audit: {audit_id})"
    )

    # Narration step 1: Network interception
    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "frontend_agent",
            "message": f"Intercepting network requests for {target_url} before user consent...",
        },
    )

    # Narration step 2: AXTree consent modal inspection
    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "frontend_agent",
            "message": "Extracting and inspecting AXTree for unbundled consent options...",
        },
    )

    # Narration step 3: Withdrawal parity testing
    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "frontend_agent",
            "message": "Testing consent withdrawal parity against Section 6(4) / Rule 3(c)(i)...",
        },
    )

    if not target_url:
        logger.warning(f"[frontend_agent] No target_url provided for audit {audit_id}")
        return {"findings": []}

    # Execute web frontend compliance audit
    findings = await audit_web_frontend(
        target_url=target_url,
        governance_promises=gov_promises,
    )

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "frontend_agent",
            "message": f"Frontend browser inspection complete. Generated {len(findings)} findings.",
        },
    )

    return {"findings": findings}
