import logging
from typing import Any

logger = logging.getLogger(__name__)


def audit_dpr_portal(
    grievance_sla_days: int | None = None,
    has_nomination_flow: bool | None = None,
    consent_manager_interoperable: bool | None = None,
    api_routes: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Audits Data Principal Rights (DPR), grievance SLAs (<=90d), and nomination (FR-6)."""
    findings: list[dict[str, Any]] = []

    # 1. Audit Grievance Redressal SLA Timer (Rule 14(3) - <=90 days)
    if grievance_sla_days is not None and grievance_sla_days > 90:
        findings.append(
            {
                "agent_role": "dpr_portal_agent",
                "act_section": "DPDP Act Sec 13",
                "rules_clause": "DPDP Rules 2025 Rule 14(3)",
                "severity": "HIGH",
                "title": "Grievance Resolution SLA Exceeds Statutory 90-Day Limit",
                "description": (
                    f"Grievance redressal SLA timer is set to {grievance_sla_days} days, "
                    "exceeding the mandatory maximum window of 90 days stipulated by "
                    "DPDP Rule 14(3)."
                ),
                "evidence_snippet": f"Configured grievance_sla_days: {grievance_sla_days}",
                "remediation_suggestion": (
                    "Reconfigure grievance ticket SLA timers and escalation policies to guarantee "
                    "formal resolution within a maximum of 90 days."
                ),
            }
        )

    # 2. Audit Nomination Flow for Data Principals (Section 14)
    has_nomination = has_nomination_flow
    if has_nomination is None and api_routes:
        has_nomination = any(
            "nomination" in r.lower() or "nominee" in r.lower() for r in api_routes
        )

    if has_nomination is False:
        findings.append(
            {
                "agent_role": "dpr_portal_agent",
                "act_section": "DPDP Act Sec 14",
                "rules_clause": "DPDP Act 2023 Sec 14",
                "severity": "MEDIUM",
                "title": "Missing Nomination Workflow for Data Principals",
                "description": (
                    "No self-service interface or API route was found allowing Data Principals to "
                    "nominate a representative to exercise rights in event of death/incapacity."
                ),
                "evidence_snippet": "has_nomination_flow: False",
                "remediation_suggestion": (
                    "Add a self-service nomination management section in user account settings "
                    "per DPDP Section 14."
                ),
            }
        )

    # 3. Audit Consent Manager Interoperability (Section 6(7)–(9), Rule 4)
    has_cm_interop = consent_manager_interoperable
    if has_cm_interop is None and api_routes:
        has_cm_interop = any("consent" in r.lower() for r in api_routes)

    if has_cm_interop is False:
        findings.append(
            {
                "agent_role": "dpr_portal_agent",
                "act_section": "DPDP Act Sec 6(7)",
                "rules_clause": "DPDP Rules 2025 Rule 4",
                "severity": "LOW",
                "title": "Consent Manager Interoperability Endpoints Missing",
                "description": (
                    "Application lacks standard API hooks or endpoints for communicating with "
                    "registered Consent Managers under DPDP Section 6(7)–(9) and Rule 4."
                ),
                "evidence_snippet": "consent_manager_interoperable: False",
                "remediation_suggestion": (
                    "Implement standard consent artifact ingestion and revocation webhook handlers "
                    "to support interoperability with Board-registered Consent Managers."
                ),
            }
        )

    return findings
