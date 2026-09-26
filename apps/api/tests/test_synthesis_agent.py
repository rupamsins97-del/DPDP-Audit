import tempfile
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from apps.api.agents.graph import audit_graph
from apps.api.agents.state import AuditContextState
from apps.api.tools.compliance_scoring import calculate_compliance_index
from apps.api.tools.reconciliation import (
    generate_state_hash,
    reconcile_governance_and_findings,
    validate_statutory_citations,
)


def test_compliance_index_formula_and_domain_weights() -> None:
    """Calculates domain-weighted Compliance Index accurately from findings."""
    # 0 findings = 100% PASS
    clean_result = calculate_compliance_index([])
    assert clean_result["compliance_score"] == 100
    assert clean_result["status"] == "PASS"

    # 1 MEDIUM finding in frontend (-8 pts on frontend domain: score 92)
    # Frontend weight is 25%, others 100%: 92*0.25 + 100*0.75 = 23 + 75 = 98
    single_medium_finding = [
        {
            "agent_role": "frontend_agent",
            "act_section": "DPDP Act Sec 6(1)",
            "rules_clause": "DPDP Rules 2025 Rule 3(1)",
            "severity": "MEDIUM",
            "title": "Bundled Consent Option",
        }
    ]
    med_result = calculate_compliance_index(single_medium_finding)
    assert med_result["compliance_score"] == 98
    assert med_result["status"] == "PASS"

    # Multiple findings across domains
    multi_findings = [
        {"agent_role": "frontend_agent", "severity": "HIGH"},
        {"agent_role": "backend_agent", "severity": "HIGH"},
        {"agent_role": "policy_agent", "severity": "MEDIUM"},
        {"agent_role": "dpr_portal_agent", "severity": "LOW"},
    ]
    multi_result = calculate_compliance_index(multi_findings)
    assert 85 <= multi_result["compliance_score"] <= 95
    assert multi_result["has_critical_findings"] is False


def test_zero_tolerance_critical_cap_forces_59_percent() -> None:
    """Presence of ANY CRITICAL finding hard-caps the final Compliance Index at 59% (FAIL)."""
    # Only 1 CRITICAL finding on frontend:
    # Raw frontend score = 100 - 30 = 70.
    # Raw composite = 70*0.25 + 100*0.75 = 17.5 + 75 = 92.5 (would normally be ~93%).
    critical_findings = [
        {
            "agent_role": "frontend_agent",
            "act_section": "DPDP Act Sec 6(1)",
            "rules_clause": "DPDP Rules 2025 Rule 3(2)",
            "severity": "CRITICAL",
            "title": "Pre-Consent Meta Pixel Fire",
        }
    ]

    result = calculate_compliance_index(critical_findings)
    assert result["has_critical_findings"] is True
    assert result["is_critical_capped"] is True
    assert result["compliance_score"] == 59
    assert result["status"] == "FAIL"


def test_statutory_misrepresentation_cross_referencing() -> None:
    """Policy promise vs tracking contradiction produces Statutory Misrepresentation."""
    governance_promises = [
        {
            "no_pre_consent_trackers": True,
            "declared_trackers": ["Google Analytics"],
            "dpo_email": "dpo@company.com",
        }
    ]

    technical_findings = [
        {
            "agent_role": "frontend_agent",
            "act_section": "DPDP Act Sec 6(1)",
            "rules_clause": "DPDP Rules 2025 Rule 3(2)",
            "severity": "CRITICAL",
            "title": "Pre-Consent Third-Party Tracker Fired: Meta Pixel",
            "description": "Network request fired before affirmative consent.",
        }
    ]

    reconciled = reconcile_governance_and_findings(
        governance_promises=governance_promises,
        findings=technical_findings,
    )

    assert len(reconciled) == 1
    misrep = reconciled[0]
    assert misrep["agent_role"] == "synthesis_agent"
    assert misrep["act_section"] == "DPDP Act Sec 6(1)"
    assert misrep["severity"] == "CRITICAL"
    assert "Statutory Misrepresentation" in misrep["title"]


def test_statutory_grounding_invariant_3_validation() -> None:
    """validate_statutory_citations enforces non-empty act_section and rules_clause."""
    valid_findings = [
        {
            "title": "Unencrypted PII Logging",
            "act_section": "DPDP Act Sec 8(5)",
            "rules_clause": "DPDP Act 2023 Sec 8(5)",
        }
    ]
    is_valid, errors = validate_statutory_citations(valid_findings)
    assert is_valid is True
    assert len(errors) == 0

    invalid_findings = [
        {
            "title": "Ungrounded finding",
            "act_section": "",
            "rules_clause": None,
        }
    ]
    is_invalid, err_list = validate_statutory_citations(invalid_findings)
    assert is_invalid is False
    assert len(err_list) == 2


def test_sha256_state_hash_generation() -> None:
    """generate_state_hash produces deterministic 64-char SHA-256 hash."""
    state_sample: dict[str, Any] = {
        "audit_id": "test-audit-123",
        "organization_id": "org-456",
        "project_name": "Acme Portal",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "compliance_score": 75,
        "findings": [{"title": "Pre-Consent Pixel"}],
        "generated_patches": [],
    }

    hash_1 = generate_state_hash(state_sample)
    hash_2 = generate_state_hash(state_sample)

    assert len(hash_1) == 64
    assert hash_1 == hash_2  # Deterministic


@pytest.mark.asyncio
async def test_end_to_end_parallel_graph_execution() -> None:
    """Executes the full parallel DAG end-to-end and verifies complete synthesis state."""
    audit_id = str(uuid4())
    org_id = str(uuid4())

    initial_state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Full Synthesis Test",
        "target_url": "https://example.com",
        "repository_url": "https://github.com/mock/repo",
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    @contextmanager
    def mock_ephemeral_clone(url: str | None):
        with tempfile.TemporaryDirectory() as td:
            yield td

    with patch("apps.api.agents.backend_agent.ephemeral_clone", mock_ephemeral_clone):
        final_state = await audit_graph.ainvoke(initial_state)

    assert final_state["status"] == "COMPLETED"
    assert final_state["compliance_score"] is not None
    assert 0 <= final_state["compliance_score"] <= 100
    assert final_state["state_hash"] is not None
    assert len(final_state["state_hash"]) == 64
    assert isinstance(final_state["findings"], list)
