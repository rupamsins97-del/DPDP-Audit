import logging
from typing import Any

logger = logging.getLogger(__name__)

# Statutory Domain Weights for Composite Compliance Index (Total = 1.0)
DOMAIN_WEIGHTS: dict[str, float] = {
    "frontend": 0.25,      # Frontend Consent & Tracking: 25%
    "backend": 0.25,       # Backend PII Security & Plaintext Logging: 25%
    "policy": 0.20,        # Legal Governance & DPA Alignment: 20%
    "child_safety": 0.10,  # Children's Data Protection: 10%
    "incident": 0.10,      # Incident Management & 72h SLA: 10%
    "dpr_portal": 0.10,    # DPR & Grievance Redressal: 10%
}

# Penalty Deductions per finding severity
SEVERITY_DEDUCTIONS: dict[str, float] = {
    "CRITICAL": 30.0,
    "HIGH": 15.0,
    "MEDIUM": 8.0,
    "LOW": 3.0,
}

# Agent Role to Domain Mapping
ROLE_TO_DOMAIN: dict[str, str] = {
    "frontend_agent": "frontend",
    "frontend": "frontend",
    "backend_agent": "backend",
    "backend": "backend",
    "policy_agent": "policy",
    "policy": "policy",
    "child_safety_agent": "child_safety",
    "child_safety": "child_safety",
    "incident_management_agent": "incident",
    "incident": "incident",
    "dpr_portal_agent": "dpr_portal",
    "dpr_portal": "dpr_portal",
    "synthesis_agent": "policy",
}


def calculate_compliance_index(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculates the composite DPDP Compliance Index (0-100%) using domain-weighted deductions.

    Enforces the Zero-Tolerance Critical Cap: if any CRITICAL finding is present, the final
    score is hard-capped at 59% (FAIL).
    """
    # 1. Initialize domain scores at baseline 100.0
    domain_deductions: dict[str, float] = {d: 0.0 for d in DOMAIN_WEIGHTS}
    domain_findings_count: dict[str, int] = {d: 0 for d in DOMAIN_WEIGHTS}
    has_critical = False

    for finding in findings:
        role = str(finding.get("agent_role", "")).lower()
        severity = str(finding.get("severity", "")).upper()
        domain = ROLE_TO_DOMAIN.get(role, "policy")

        deduction = SEVERITY_DEDUCTIONS.get(severity, 0.0)
        domain_deductions[domain] += deduction
        domain_findings_count[domain] += 1

        if severity == "CRITICAL":
            has_critical = True

    # 2. Compute individual domain scores (bounded [0, 100])
    domain_scores: dict[str, float] = {}
    for domain in DOMAIN_WEIGHTS:
        raw_domain_score = 100.0 - domain_deductions[domain]
        domain_scores[domain] = max(0.0, min(100.0, raw_domain_score))

    # 3. Compute domain-weighted composite score
    raw_composite = sum(
        domain_scores[d] * DOMAIN_WEIGHTS[d] for d in DOMAIN_WEIGHTS
    )
    rounded_composite = round(raw_composite)

    # 4. Apply Zero-Tolerance Critical Cap
    if has_critical and rounded_composite > 59:
        final_score = 59
        is_capped = True
    else:
        final_score = max(0, min(100, int(rounded_composite)))
        is_capped = False

    # 5. Determine statutory status
    if final_score >= 80:
        compliance_status = "PASS"
    elif final_score >= 60:
        compliance_status = "WARN"
    else:
        compliance_status = "FAIL"

    return {
        "compliance_score": final_score,
        "raw_composite_score": round(raw_composite, 2),
        "status": compliance_status,
        "is_critical_capped": is_capped,
        "has_critical_findings": has_critical,
        "domain_scores": domain_scores,
        "domain_deductions": domain_deductions,
        "domain_findings_count": domain_findings_count,
    }
