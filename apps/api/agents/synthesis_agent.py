import logging
from typing import Any

from apps.api.agents.state import AuditContextState
from apps.api.tools.compliance_scoring import calculate_compliance_index
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.reconciliation import (
    generate_state_hash,
    reconcile_governance_and_findings,
    validate_statutory_citations,
)

logger = logging.getLogger(__name__)


async def synthesis_init_node(state: AuditContextState) -> dict[str, Any]:
    """Synthesis Agent entry node: initializes audit context and coordinates workers."""
    audit_id = state.get("audit_id", "unknown-audit")
    logger.info(f"[synthesis_agent] Initializing compliance audit {audit_id}")

    event_bus = get_event_bus()
    await event_bus.publish(
        "AUDIT_STARTED",
        {
            "audit_id": audit_id,
            "project_name": state.get("project_name"),
            "target_url": state.get("target_url"),
            "status": "IN_PROGRESS",
        },
    )

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "synthesis_agent",
            "message": "Initializing 360° compliance audit DAG and dispatching policy analysis...",
        },
    )

    return {"status": "IN_PROGRESS"}


async def synthesis_reconcile_node(state: AuditContextState) -> dict[str, Any]:
    """Synthesis Agent exit node: reconciles promises vs reality, computes score and state hash."""
    audit_id = state.get("audit_id", "unknown-audit")
    current_findings = list(state.get("findings") or [])
    gov_promises = list(state.get("governance_promises") or [])
    event_bus = get_event_bus()

    logger.info(f"[synthesis_agent] Reconciling findings for audit {audit_id}")

    # Narration step 1: Reconciliation
    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "synthesis_agent",
            "message": "Reconciling policy governance promises against technical reality...",
        },
    )

    # 1. Perform promise-vs-reality cross-referencing (Statutory Misrepresentation detection)
    reconciled_findings = reconcile_governance_and_findings(
        governance_promises=gov_promises,
        findings=current_findings,
    )

    all_findings = current_findings + reconciled_findings

    # 2. Enforce Invariant 3: Verify statutory grounding on all findings
    is_valid, citation_errors = validate_statutory_citations(all_findings)
    if not is_valid:
        logger.warning(
            f"[synthesis_agent] Citation warnings detected in audit {audit_id}: {citation_errors}"
        )

    # 3. Compute domain-weighted DPDP Compliance Index with Zero-Tolerance Critical Cap
    scoring_result = calculate_compliance_index(all_findings)
    final_score = scoring_result["compliance_score"]

    # 4. Generate deterministic SHA-256 state hash for NFR-3 immutable audit trail
    state_for_hash = dict(state)
    state_for_hash["findings"] = all_findings
    state_for_hash["compliance_score"] = final_score
    state_hash = generate_state_hash(state_for_hash)

    # Narration step 2: Finalization
    score_status = scoring_result["status"]
    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "synthesis_agent",
            "message": (
                f"Compliance synthesis complete. Index: {final_score}% [{score_status}], "
                f"Total Findings: {len(all_findings)}, State Hash: {state_hash[:12]}..."
            ),
        },
    )

    await event_bus.publish(
        "AUDIT_COMPLETED",
        {
            "audit_id": audit_id,
            "status": "COMPLETED",
            "compliance_score": final_score,
            "state_hash": state_hash,
            "findings_count": len(all_findings),
        },
    )

    return {
        "status": "COMPLETED",
        "compliance_score": final_score,
        "state_hash": state_hash,
        "findings": reconciled_findings,
    }
