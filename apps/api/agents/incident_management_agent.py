import logging
from typing import Any

from apps.api.agents.state import AuditContextState
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.incident_scanner import audit_incident_management

logger = logging.getLogger(__name__)


async def incident_management_agent_node(state: AuditContextState) -> dict[str, Any]:
    """Incident Management Agent: audits breach response playbooks and 72h DPB pipelines."""
    audit_id = state.get("audit_id", "unknown-audit")
    event_bus = get_event_bus()

    logger.info(f"[incident_management_agent] Evaluating breach readiness for audit {audit_id}")

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "incident_management_agent",
            "message": "Inspecting incident response playbooks for 72h DPB breach notification...",
        },
    )

    uploaded_docs = state.get("uploaded_documents") or []
    playbook_text: str | None = None
    playbook_bytes: bytes | None = None

    for doc in uploaded_docs:
        if isinstance(doc, dict):
            filename = str(doc.get("filename", "")).lower()
            if "breach" in filename or "incident" in filename or "playbook" in filename:
                playbook_bytes = doc.get("content_bytes")
                playbook_text = doc.get("content_text")
                break

    findings = audit_incident_management(
        playbook_text=playbook_text,
        playbook_pdf_bytes=playbook_bytes,
    )

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "incident_management_agent",
            "message": f"Incident management audit complete. Generated {len(findings)} findings.",
        },
    )

    return {"findings": findings}
