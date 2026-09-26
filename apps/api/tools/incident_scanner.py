import logging
import re
from typing import Any

from apps.api.tools.pdf_parser import extract_text_from_pdf_bytes

logger = logging.getLogger(__name__)

# Mandatory fields for DPB notification payload (Rule 7(1))
MANDATORY_BREACH_PAYLOAD_FIELDS = (
    "nature_of_breach",
    "impacted_count",
    "mitigation_steps",
)


def audit_incident_management(
    playbook_text: str | None = None,
    playbook_pdf_bytes: bytes | None = None,
    siem_alerts: list[dict[str, Any]] | None = None,
    notification_payload_schema: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Audits data breach response readiness, 72h DPB notification, and schemas (FR-4).

    Reuses extract_text_from_pdf_bytes from Unit 06 to avoid code duplication.
    """
    findings: list[dict[str, Any]] = []

    # 1. Extract text from PDF if provided (reusing Unit 06 parser)
    full_text = playbook_text or ""
    if playbook_pdf_bytes:
        pdf_text = extract_text_from_pdf_bytes(playbook_pdf_bytes)
        full_text = f"{full_text}\n{pdf_text}" if full_text else pdf_text

    text_lower = full_text.lower()

    # 2. Audit 72-Hour DPB Notification Pipeline (Rule 7(2))
    has_72h_dpb = False
    if "72 hour" in text_lower or "72-hour" in text_lower or "72h" in text_lower:
        if any(dpb in text_lower for dpb in ("data protection board", "dpb", "board")):
            has_72h_dpb = True

    # Check for excessive SLA numbers (e.g. 5 days, 7 days, 14 days, 30 days)
    has_excessive_sla = False
    sla_pattern = r"(\d+)\s*(?:days?|working days?)\s*(?:to notify|for reporting|breach notice)"
    excessive_matches = re.findall(sla_pattern, text_lower)
    for match in excessive_matches:
        if int(match) > 3:  # 72 hours = 3 days
            has_excessive_sla = True

    if (not has_72h_dpb or has_excessive_sla) and full_text:
        findings.append(
            {
                "agent_role": "incident_management_agent",
                "act_section": "DPDP Act Sec 8(6)",
                "rules_clause": "DPDP Rules 2025 Rule 7(2)",
                "severity": "CRITICAL",
                "title": "Missing or Non-Compliant 72-Hour DPB Breach Notification Pipeline",
                "description": (
                    "Incident response protocol does not mandate or automate intimation to the "
                    "Data Protection Board of India within 72 hours of confirming a personal data "
                    "breach, violating DPDP Section 8(6) and Rule 7(2)."
                ),
                "evidence_snippet": (
                    f"Playbook Excerpt: '{full_text[:200]}...'"
                    if full_text
                    else "No 72-hour DPB pipeline defined."
                ),
                "remediation_suggestion": (
                    "Implement an automated breach alerting workflow configuring mandatory "
                    "intimation to the DPB within 72 hours of breach confirmation."
                ),
            }
        )

    # 3. Audit Notification Payload Schema (Rule 7(1))
    if notification_payload_schema:
        schema_keys = {k.lower() for k in notification_payload_schema.keys()}
        missing_fields = []
        for req_field in MANDATORY_BREACH_PAYLOAD_FIELDS:
            clean_req = req_field.replace("_", "")
            matches = [k for k in schema_keys if clean_req in k.replace("_", "")]
            if req_field not in schema_keys and not matches:
                missing_fields.append(req_field)

        if missing_fields:
            missing_str = ", ".join(missing_fields)
            keys_preview = list(notification_payload_schema.keys())
            findings.append(
                {
                    "agent_role": "incident_management_agent",
                    "act_section": "DPDP Act Sec 8(6)",
                    "rules_clause": "DPDP Rules 2025 Rule 7(1)",
                    "severity": "HIGH",
                    "title": "Incomplete Breach Notification Payload Schema",
                    "description": (
                        "Breach notification payload schema is missing mandatory statutory fields: "
                        f"{missing_fields}. DPDP Rule 7(1) requires nature of breach, impacted "
                        "count, and mitigation steps."
                    ),
                    "evidence_snippet": f"Payload schema keys: {keys_preview}",
                    "remediation_suggestion": (
                        f"Add required fields ({missing_str}) to the automated breach "
                        "reporting data structure."
                    ),
                }
            )

    return findings
