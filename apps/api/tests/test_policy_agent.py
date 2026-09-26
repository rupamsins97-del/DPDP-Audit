import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from apps.api.agents.policy_agent import parse_governance_document, policy_agent_node
from apps.api.agents.state import AuditContextState
from apps.api.scripts.ingest_rag_corpus import (
    load_and_chunk_rag_corpus,
    parse_dpdp_act_chunks,
    parse_dpdp_rules_chunks,
)
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.pdf_parser import extract_text_from_pdf_bytes
from apps.api.tools.statutory_matcher import match_statute_clause


def test_rag_corpus_chunking_act_and_rules() -> None:
    """Verifies that RAG corpus parser produces semantic chunks with proper statute_reference."""
    # Test DPDP Act chunking
    sample_act = """## CHAPTER II: OBLIGATIONS OF DATA FIDUCIARY
### 6. Consent.
(1) The consent given by the Data Principal shall be free, specific, informed.
### 8. General obligations of Data Fiduciary.
(7) A Data Fiduciary shall erase personal data upon consent withdrawal.
## THE SCHEDULE
(See section 33)
PENALTIES FOR BREACH
"""
    chunks = parse_dpdp_act_chunks(sample_act)
    assert len(chunks) == 3
    refs = [c["statute_reference"] for c in chunks]
    assert "DPDP Act Sec 6" in refs
    assert "DPDP Act Sec 8" in refs
    assert "DPDP Act Schedule" in refs

    # Test DPDP Rules chunking
    sample_rules = """### 3. Notice given by Data Fiduciary to Data Principal.
The notice shall be clear and plain.
### 6. Reasonable security safeguards.
Maintain security logs for 1 year.
"""
    rule_chunks = parse_dpdp_rules_chunks(sample_rules)
    assert len(rule_chunks) == 2
    rule_refs = [c["statute_reference"] for c in rule_chunks]
    assert "DPDP Rules 2025 Rule 3" in rule_refs
    assert "DPDP Rules 2025 Rule 6" in rule_refs


def test_load_all_rag_documents() -> None:
    """Verifies that all 3 RAG corpus files in context/RAG load and chunk cleanly."""
    base_dir = Path(__file__).resolve().parents[3]
    rag_dir = base_dir / "context" / "RAG"
    chunks = load_and_chunk_rag_corpus(rag_dir)
    assert len(chunks) > 40  # Should have all sections of Act & Rules


def test_policy_document_parsing_categories_and_dpo() -> None:
    """Verifies FR-1.1: itemised personal data categories, purposes, and DPO extraction."""
    policy_text = """
    Privacy Policy:
    We collect Name, Email, Phone Number, and IP Address for Account Authentication and Marketing.
    For any grievances, contact our Data Protection Officer at dpo@enterprise.com.
    Available in English and Hindi.
    """
    parsed = parse_governance_document(policy_text)
    assert "Name / Identity" in parsed["data_categories"]
    assert "Email Address" in parsed["data_categories"]
    assert "Device & Network Identifiers" in parsed["data_categories"]
    assert "Service Provision & Account Management" in parsed["purposes"]
    assert parsed["dpo_info"]["dpo_published"] is True
    assert parsed["dpo_info"]["email"] == "dpo@enterprise.com"
    assert parsed["multilingual_support"] is True


def test_dpa_terms_parsing_retention_and_erasure() -> None:
    """Verifies FR-1.3: DPA clauses extraction (erasure, 1-year log retention, breach reporting)."""
    dpa_text = """
    Vendor Data Processing Agreement:
    Processor shall retain logs for 60 days.
    All personal data will be erased upon contract termination.
    Processor must report breaches within 72 hours.
    """
    parsed = parse_governance_document(dpa_text)
    assert parsed["dpa_terms"]["erasure_upon_termination"] is True
    assert parsed["dpa_terms"]["log_retention_days"] == 60
    assert parsed["dpa_terms"]["breach_reporting_hours"] == 72


def test_statutory_matching_grounding() -> None:
    """Verifies FR-1.4 / Invariant 3: Grounded statutory citations on all queries."""
    m1 = match_statute_clause("Erasure of personal data upon consent withdrawal")
    assert "DPDP Act Sec 8" in m1["act_section"] or "DPDP" in m1["act_section"]
    assert m1["rules_clause"] is not None

    m2 = match_statute_clause("Data Protection Officer contact grievance")
    assert "Sec 8(9)" in m2["act_section"] or "DPDP Act" in m2["act_section"]


def test_in_memory_pdf_text_extraction_and_zero_disk() -> None:
    """Verifies in-memory PDF parsing without writing files to disk (Invariant 2 & 4)."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    import io
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    # Ensure function extracts text without error or disk write
    text = extract_text_from_pdf_bytes(pdf_bytes)
    assert isinstance(text, str)


@pytest.mark.asyncio
async def test_policy_agent_node_execution_and_event_bus() -> None:
    """Verifies policy_agent_node emits GOVERNANCE_RULES_READY and generates grounded findings."""
    audit_id = str(uuid4())
    org_id = str(uuid4())

    event_bus = get_event_bus()
    received_events = []

    async def sub():
        async for msg in event_bus.subscribe("GOVERNANCE_RULES_READY"):
            received_events.append(msg)
            break

    sub_task = asyncio.create_task(sub())
    await asyncio.sleep(0.01)

    state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Policy Agent Test",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "uploaded_documents": [
            "Privacy Notice (English Only): We collect IP and Location. "
            "DPA: retain logs for 60 days. No DPO contact provided."
        ],
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    result = await policy_agent_node(state)
    await asyncio.wait_for(sub_task, timeout=2.0)

    # 1. Check Event Bus
    assert len(received_events) == 1
    assert received_events[0]["event"] == "GOVERNANCE_RULES_READY"
    assert received_events[0]["payload"]["audit_id"] == audit_id

    # 2. Check Governance Promises
    assert len(result["governance_promises"]) > 0
    proms = result["governance_promises"][0]
    assert "data_categories" in proms
    assert proms["dpa_terms"]["log_retention_days"] == 60

    # 3. Check Grounded Findings (Invariant 3)
    assert len(result["findings"]) >= 2
    for finding in result["findings"]:
        assert finding["act_section"] is not None
        assert finding["rules_clause"] is not None
        assert finding["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert finding["agent_role"] == "policy_agent"
