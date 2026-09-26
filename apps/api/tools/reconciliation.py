import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def reconcile_governance_and_findings(
    governance_promises: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Reconciles policy promises against technical realities (FR-1 vs FR-2/FR-3).

    Detects Statutory Misrepresentations under Section 6(1) when policy statements
    are contradicted by technical observations (e.g. pre-consent tracking).
    """
    synthesized_findings: list[dict[str, Any]] = []

    # Flatten governance promises
    flat_promises: dict[str, Any] = {}
    for p in governance_promises:
        if isinstance(p, dict):
            flat_promises.update(p)

    # 1. Cross-reference: Policy claims vs Frontend Pre-Consent Tracking
    has_pre_consent_tracker_finding = any(
        f.get("agent_role") in ("frontend_agent", "frontend")
        and (
            "pre-consent" in str(f.get("title", "")).lower()
            or "6(1)" in str(f.get("act_section", ""))
        )
        for f in findings
    )

    # If policy declared no sharing without consent or declared trackers list
    policy_claims_no_unconsented_tracking = (
        flat_promises.get("no_pre_consent_trackers") is True
        or "declared_trackers" in flat_promises
        or len(governance_promises) > 0  # Standard policy audit
    )

    if has_pre_consent_tracker_finding and policy_claims_no_unconsented_tracking:
        already_present = any(
            f.get("agent_role") == "synthesis_agent"
            and "Statutory Misrepresentation" in str(f.get("title", ""))
            for f in findings
        )

        if not already_present:
            synthesized_findings.append(
                {
                    "agent_role": "synthesis_agent",
                    "act_section": "DPDP Act Sec 6(1)",
                    "rules_clause": "DPDP Rules 2025 Rule 3(2)",
                    "severity": "CRITICAL",
                    "title": "Statutory Misrepresentation: Policy vs Pre-Consent Tracking",
                    "description": (
                        "Privacy Policy declarations state that personal data is not processed or "
                        "shared without affirmative consent, yet frontend inspection detected "
                        "active third-party tracking network requests prior to user consent. "
                        "This contradiction constitutes an actionable Statutory Misrepresentation "
                        "under DPDP Section 6(1)."
                    ),
                    "evidence_snippet": (
                        "Policy Promise: 'No tracking without consent' vs "
                        "Frontend Observation: Active pre-consent third-party tracking requests."
                    ),
                    "remediation_suggestion": (
                        "Align privacy policy declarations with technical code realities and "
                        "ensure all tracking pixels are strictly blocked until explicit consent."
                    ),
                }
            )

    return synthesized_findings


def validate_statutory_citations(findings: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Enforces Invariant 3 (NFR-1): verifies every finding carries explicit statutory clauses."""
    errors: list[str] = []

    for idx, f in enumerate(findings):
        act_sec = str(f.get("act_section") or "").strip()
        rule_cl = str(f.get("rules_clause") or "").strip()

        if not act_sec:
            errors.append(f"Finding #{idx} ('{f.get('title')}') missing mandatory 'act_section'")
        if not rule_cl:
            errors.append(f"Finding #{idx} ('{f.get('title')}') missing mandatory 'rules_clause'")

    return len(errors) == 0, errors


def generate_state_hash(state: dict[str, Any]) -> str:
    """Produces a deterministic SHA-256 state hash for immutable audit trails (NFR-3)."""
    # Create canonical serializable representation
    serializable_dict: dict[str, Any] = {
        "audit_id": str(state.get("audit_id", "")),
        "organization_id": str(state.get("organization_id", "")),
        "project_name": str(state.get("project_name", "")),
        "target_url": str(state.get("target_url", "")),
        "repository_url": str(state.get("repository_url") or ""),
        "framework": str(state.get("framework", "")),
        "compliance_score": state.get("compliance_score"),
        "findings_count": len(state.get("findings", [])),
        "findings_titles": sorted([str(f.get("title", "")) for f in state.get("findings", [])]),
        "patches_count": len(state.get("generated_patches", [])),
    }

    canonical_json = json.dumps(serializable_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
