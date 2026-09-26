import logging
from typing import Any

from apps.api.tools.axtree_parser import flatten_axtree

logger = logging.getLogger(__name__)

# Recognized Verifiable Parental Consent (VPC) identity mechanisms under Rule 10
APPROVED_VPC_MECHANISMS = (
    "digilocker",
    "aadhaar virtual token",
    "aadhaar token",
    "vpc token",
    "parental kyc",
    "government id",
)

AGE_GATING_KEYWORDS = (
    "age verification",
    "date of birth",
    "enter age",
    "parental consent",
    "age gate",
)


def audit_child_safety(
    axtree_snapshot: dict[str, Any] | list[dict[str, Any]] | None = None,
    has_age_gating: bool | None = None,
    minor_tracking_excluded: bool | None = None,
    vpc_mechanism: str | None = None,
) -> list[dict[str, Any]]:
    """Audits age-gating, Verifiable Parental Consent (VPC), and minor tracking exclusion (FR-5).

    Reuses flatten_axtree from Unit 08's axtree_parser to avoid duplicate DOM/browser logic.
    """
    findings: list[dict[str, Any]] = []

    # 1. Inspect Age-Gating and Rule 10 VPC Mechanisms
    has_age_gate_ui = False
    has_vpc_ui = False

    if axtree_snapshot:
        flat_nodes = flatten_axtree(axtree_snapshot)
        node_texts = " ".join(
            [str(n.get("name", "")) + " " + str(n.get("role", "")) for n in flat_nodes]
        ).lower()

        if any(term in node_texts for term in AGE_GATING_KEYWORDS):
            has_age_gate_ui = True

        if any(mech in node_texts for mech in APPROVED_VPC_MECHANISMS):
            has_vpc_ui = True

    # Check explicit flag or UI detection
    age_gate_effective = has_age_gating if has_age_gating is not None else has_age_gate_ui
    vpc_effective = (
        (vpc_mechanism.lower() in APPROVED_VPC_MECHANISMS)
        if vpc_mechanism
        else has_vpc_ui
    )

    if not age_gate_effective or not vpc_effective:
        findings.append(
            {
                "agent_role": "child_safety_agent",
                "act_section": "DPDP Act Sec 9(1)",
                "rules_clause": "DPDP Rules 2025 Rule 10",
                "severity": "CRITICAL",
                "title": "Missing Age-Gating & Verifiable Parental Consent (VPC) Mechanism",
                "description": (
                    "No verifiable age-gating interface or approved Verifiable Parental Consent "
                    "(VPC) identity mechanism (e.g. DigiLocker / Aadhaar Virtual Token) was "
                    "detected, violating DPDP Section 9(1) and Rule 10."
                ),
                "evidence_snippet": (
                    f"Age Gating: {age_gate_effective} | VPC Mechanism: {vpc_mechanism or 'None'}"
                ),
                "remediation_suggestion": (
                    "Implement an age-assurance checkpoint and integrate approved Rule 10 VPC "
                    "mechanisms (e.g. DigiLocker) before processing children's personal data."
                ),
            }
        )

    # 2. Check Minor Behavioral Tracking Exclusion (Section 9(3))
    if minor_tracking_excluded is False:
        findings.append(
            {
                "agent_role": "child_safety_agent",
                "act_section": "DPDP Act Sec 9(3)",
                "rules_clause": "DPDP Act 2023 Sec 9(3)",
                "severity": "CRITICAL",
                "title": "Prohibited Behavioral Tracking or Targeted Advertising on Minors",
                "description": (
                    "Ad-tech tracking or behavioral profiling scripts are active without filtering "
                    "accounts of minors (<18 years), directly violating DPDP Section 9(3)."
                ),
                "evidence_snippet": "minor_tracking_excluded: False",
                "remediation_suggestion": (
                    "Implement a strict suppression rule excluding identified minors from all "
                    "ad-tech tracking, behavioral profiling, and targeted recommendation systems."
                ),
            }
        )

    return findings
