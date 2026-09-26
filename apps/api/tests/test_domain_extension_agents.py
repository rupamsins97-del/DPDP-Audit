import asyncio
from typing import Any
from uuid import uuid4

import pytest
from apps.api.agents.child_safety_agent import child_safety_agent_node
from apps.api.agents.dpr_portal_agent import dpr_portal_agent_node
from apps.api.agents.incident_management_agent import incident_management_agent_node
from apps.api.agents.state import AuditContextState
from apps.api.tools.child_safety_scanner import audit_child_safety
from apps.api.tools.dpr_portal_scanner import audit_dpr_portal
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.incident_scanner import audit_incident_management


def test_breach_playbook_missing_72h_pipeline_flagged_rule_7_2() -> None:
    """A breach response playbook missing the 72-hour DPB pipeline is flagged (FR-4.1)."""
    # Non-compliant playbook with 14-day reporting timeline
    non_compliant_playbook = (
        "Acme Corp Security Incident Response Plan:\n"
        "In the event of a suspected data breach, the Security Team will investigate.\n"
        "Management will notify regulatory authorities within 14 working days."
    )

    findings = audit_incident_management(playbook_text=non_compliant_playbook)
    assert len(findings) >= 1

    first = findings[0]
    assert first["agent_role"] == "incident_management_agent"
    assert first["act_section"] == "DPDP Act Sec 8(6)"
    assert "Rule 7(2)" in first["rules_clause"]
    assert first["severity"] == "CRITICAL"
    assert "72-Hour DPB Breach Notification" in first["title"]

    # Compliant playbook with explicit 72-hour DPB notice
    compliant_playbook = (
        "Acme Corp Security Incident Response Plan:\n"
        "Upon confirming any personal data breach, the DPO will notify the Data Protection Board "
        "(DPB) of India within 72 hours per DPDP Rule 7(2), and intimate all impacted Principals."
    )
    compliant_findings = audit_incident_management(playbook_text=compliant_playbook)
    assert len(compliant_findings) == 0


def test_breach_payload_schema_missing_required_fields() -> None:
    """Notification payload schema missing required fields is flagged under Rule 7(1)."""
    incomplete_schema = {
        "timestamp": "2026-09-26T12:00:00Z",
        "affected_system": "user-db-primary",
        # Missing nature_of_breach, impacted_count, mitigation_steps
    }

    findings = audit_incident_management(
        playbook_text="We notify the Data Protection Board within 72 hours.",
        notification_payload_schema=incomplete_schema,
    )

    schema_findings = [f for f in findings if "Payload Schema" in f["title"]]
    assert len(schema_findings) == 1
    assert schema_findings[0]["act_section"] == "DPDP Act Sec 8(6)"
    assert "Rule 7(1)" in schema_findings[0]["rules_clause"]
    assert schema_findings[0]["severity"] == "HIGH"


def test_missing_age_gating_flagged_section_9_rule_10() -> None:
    """Site with no age-gating or VPC mechanism is flagged under Sec 9 / Rule 10 (FR-5.1)."""
    # Case 1: No age gating and no VPC mechanism
    findings = audit_child_safety(
        has_age_gating=False,
        vpc_mechanism=None,
    )
    assert len(findings) >= 1
    vpc_finding = findings[0]
    assert vpc_finding["agent_role"] == "child_safety_agent"
    assert vpc_finding["act_section"] == "DPDP Act Sec 9(1)"
    assert "Rule 10" in vpc_finding["rules_clause"]
    assert vpc_finding["severity"] == "CRITICAL"
    assert "Verifiable Parental Consent" in vpc_finding["title"]

    # Case 2: Tracking on minors is not excluded (FR-5.2)
    minor_tracking_findings = audit_child_safety(
        has_age_gating=True,
        vpc_mechanism="DigiLocker",
        minor_tracking_excluded=False,
    )
    assert len(minor_tracking_findings) == 1
    tracking_finding = minor_tracking_findings[0]
    assert tracking_finding["act_section"] == "DPDP Act Sec 9(3)"
    assert tracking_finding["severity"] == "CRITICAL"
    assert "Prohibited Behavioral Tracking" in tracking_finding["title"]

    # Case 3: Fully compliant child safety implementation
    compliant_findings = audit_child_safety(
        has_age_gating=True,
        vpc_mechanism="DigiLocker",
        minor_tracking_excluded=True,
    )
    assert len(compliant_findings) == 0


def test_axtree_age_gate_detection_reuses_axtree() -> None:
    """child_safety_scanner reuses AXTree structures without separate browser sessions."""
    mock_axtree: dict[str, Any] = {
        "role": "dialog",
        "name": "Age Verification Checkpoint",
        "children": [
            {
                "role": "button",
                "name": "Verify Parent with DigiLocker",
            },
        ],
    }

    findings = audit_child_safety(axtree_snapshot=mock_axtree)
    assert len(findings) == 0


def test_grievance_portal_120d_sla_flagged_rule_14_3() -> None:
    """Grievance portal with 120-day SLA timer is flagged under Rule 14(3) (FR-6.1)."""
    # Non-compliant: 120-day SLA (statutory limit is <=90 days)
    findings = audit_dpr_portal(grievance_sla_days=120)

    assert len(findings) == 1
    sla_finding = findings[0]
    assert sla_finding["agent_role"] == "dpr_portal_agent"
    assert sla_finding["act_section"] == "DPDP Act Sec 13"
    assert "Rule 14(3)" in sla_finding["rules_clause"]
    assert sla_finding["severity"] == "HIGH"
    assert "90-Day Limit" in sla_finding["title"]
    assert "120 days" in sla_finding["description"]

    # Compliant: 30-day SLA
    compliant_findings = audit_dpr_portal(grievance_sla_days=30)
    assert len(compliant_findings) == 0


def test_nomination_flow_and_consent_manager_checks() -> None:
    """DPR scanner audits nomination flow (Sec 14) and Consent Manager interoperability."""
    findings = audit_dpr_portal(
        grievance_sla_days=45,
        has_nomination_flow=False,
        consent_manager_interoperable=False,
    )

    assert len(findings) == 2
    nom_finding = next(f for f in findings if f["act_section"] == "DPDP Act Sec 14")
    assert "Nomination Workflow" in nom_finding["title"]
    assert nom_finding["severity"] == "MEDIUM"

    cm_finding = next(f for f in findings if f["act_section"] == "DPDP Act Sec 6(7)")
    assert "Consent Manager Interoperability" in cm_finding["title"]
    assert "Rule 4" in cm_finding["rules_clause"]


@pytest.mark.asyncio
async def test_extension_agents_execute_and_emit_telemetry() -> None:
    """All 3 domain extension agent nodes execute in LangGraph and emit telemetry."""
    audit_id = str(uuid4())
    org_id = str(uuid4())
    event_bus = get_event_bus()

    telemetry_messages: list[str] = []

    async def log_subscriber():
        async for msg in event_bus.subscribe("TELEMETRY_LOG"):
            if msg.get("payload", {}).get("audit_id") == audit_id:
                telemetry_messages.append(msg["payload"]["message"])

    task = asyncio.create_task(log_subscriber())
    await asyncio.sleep(0.01)

    state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Domain Extensions Test",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "uploaded_documents": [
            {
                "filename": "incident_playbook.txt",
                "content_text": "Breach notification to board within 14 days.",
            }
        ],
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    # Run all 3 nodes
    res_inc = await incident_management_agent_node(state)
    res_cs = await child_safety_agent_node(state)
    res_dpr = await dpr_portal_agent_node(state)

    await asyncio.sleep(0.05)
    task.cancel()

    assert "findings" in res_inc
    assert len(res_inc["findings"]) >= 1
    assert res_inc["findings"][0]["agent_role"] == "incident_management_agent"

    assert "findings" in res_cs
    assert isinstance(res_cs["findings"], list)

    assert "findings" in res_dpr
    assert isinstance(res_dpr["findings"], list)

    assert len(telemetry_messages) >= 3
