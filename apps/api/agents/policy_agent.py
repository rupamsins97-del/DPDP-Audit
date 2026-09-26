import logging
import re
from typing import Any

from apps.api.agents.state import AuditContextState
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.pdf_parser import extract_text_from_pdf_bytes
from apps.api.tools.statutory_matcher import match_statute_clause

logger = logging.getLogger(__name__)

EIGHTH_SCHEDULE_LANGUAGES = {
    "assamese", "bengali", "bodo", "dogri", "gujarati", "hindi", "kannada",
    "kashmiri", "konkani", "maithili", "malayalam", "manipuri", "marathi",
    "nepali", "odia", "punjabi", "sanskrit", "santali", "sindhi", "tamil",
    "telugu", "urdu"
}


def parse_governance_document(text: str) -> dict[str, Any]:
    """Extracts statutory commitments and compliance promises from legal text (FR-1.1 - FR-1.3)."""
    lower_text = text.lower()

    # 1. Personal Data Categories (FR-1.1)
    data_categories = []
    category_patterns = [
        (r"\b(name|full name|username)\b", "Name / Identity"),
        (r"\b(email|email address)\b", "Email Address"),
        (r"\b(phone|mobile|phone number)\b", "Phone / Contact Number"),
        (r"\b(ip|ip address|device id|mac address)\b", "Device & Network Identifiers"),
        (r"\b(location|geo-location|gps)\b", "Location Data"),
        (r"\b(financial|card|bank|pan|aadhaar)\b", "Financial & Government IDs"),
    ]
    for pattern, cat_name in category_patterns:
        if re.search(pattern, lower_text):
            data_categories.append(cat_name)

    # 2. Processing Purposes (FR-1.1)
    purposes = []
    purpose_patterns = [
        (r"\b(account|authentication|login|service)\b", "Service Provision & Account Management"),
        (r"\b(analytics|performance|improvement)\b", "Product Improvement & Analytics"),
        (r"\b(marketing|advertisement|promotional)\b", "Marketing & Personalization"),
        (r"\b(third-party|third party|vendor|partner)\b", "Third-Party Vendor Processing"),
    ]
    for pattern, purp_name in purpose_patterns:
        if re.search(pattern, lower_text):
            purposes.append(purp_name)

    # 3. DPO / Grievance Officer Contact Details (FR-1.1)
    dpo_info: dict[str, Any] = {"dpo_published": False, "email": None, "name": None}
    dpo_pattern = (
        r"(data protection officer|grievance officer|dpo)"
        r"[\s\S]{0,150}?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    )
    dpo_match = re.search(dpo_pattern, lower_text)
    if dpo_match:
        dpo_info["dpo_published"] = True
        dpo_info["email"] = dpo_match.group(2)
    elif any(k in lower_text for k in ("grievance", "dpo", "data protection officer")):
        email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
        if email_match:
            dpo_info["dpo_published"] = True
            dpo_info["email"] = email_match.group(1)

    # 4. Multi-lingual Support (FR-1.2)
    found_languages = []
    for lang in EIGHTH_SCHEDULE_LANGUAGES:
        if lang in lower_text:
            found_languages.append(lang.capitalize())
    # Notice available in at least one Eighth Schedule language besides English
    multilingual_support = len(found_languages) >= 1

    # 5. DPA Terms Extraction (FR-1.3)
    has_erasure = any(
        w in lower_text
        for w in ("erasure", "erase", "erased", "delete", "deleted", "destruction", "purge")
    )
    dpa_terms: dict[str, Any] = {
        "erasure_upon_termination": has_erasure,
        "log_retention_days": 365,
        "breach_reporting_hours": 72,
    }

    retention_pattern = r"retain(?:ing)?\s+(?:logs?|data)\s+for\s+(\d+)\s+days?"
    retention_match = re.search(retention_pattern, lower_text)
    if retention_match:
        dpa_terms["log_retention_days"] = int(retention_match.group(1))

    breach_match = re.search(r"report\s+breach(?:es)?\s+within\s+(\d+)\s+hours?", lower_text)
    if breach_match:
        dpa_terms["breach_reporting_hours"] = int(breach_match.group(1))

    return {
        "data_categories": data_categories or ["General Personal Data"],
        "purposes": purposes or ["Service Provision"],
        "dpo_info": dpo_info,
        "multilingual_support": multilingual_support,
        "detected_languages": found_languages,
        "dpa_terms": dpa_terms,
    }


async def policy_agent_node(state: AuditContextState) -> dict[str, Any]:
    """Policy Agent: performs deep semantic parsing on Privacy Policies & DPAs with RAG."""
    audit_id = state.get("audit_id", "unknown-audit")
    logger.info(f"[policy_agent] Executing statutory RAG governance audit for {audit_id}")

    # 1. Retrieve document content from state or sample
    doc_text = ""
    uploaded_docs = state.get("uploaded_documents") or []

    for doc in uploaded_docs:
        if isinstance(doc, dict) and "bytes" in doc:
            extracted = extract_text_from_pdf_bytes(doc["bytes"])
            doc_text += f"\n\n{extracted}"
        elif isinstance(doc, str):
            doc_text += f"\n\n{doc}"

    # Default fallback sample policy if no uploaded document
    if not doc_text.strip():
        doc_text = (
            "Privacy Policy: We collect Name, Email, IP address for authentication and analytics. "
            "Available in English and Hindi. "
            "Grievance Officer Contact: grievance@company.com. "
            "Data Processing Agreement: Vendor shall retain security logs for 365 days and report "
            "personal data breaches within 72 hours. All data erased upon contract termination."
        )

    # 2. Extract governance commitments
    gov_data = parse_governance_document(doc_text)
    findings: list[dict[str, Any]] = []

    # 3. Grounding & Rule Verification (FR-1.1 - FR-1.4)

    # Check DPO publication (DPDP Act Sec 8(9))
    if not gov_data["dpo_info"]["dpo_published"]:
        grounding = match_statute_clause("Publish contact details of Data Protection Officer DPO")
        findings.append({
            "audit_id": audit_id,
            "agent_role": "policy_agent",
            "act_section": grounding["act_section"],
            "rules_clause": grounding["rules_clause"],
            "severity": "HIGH",
            "title": "Missing DPO or Grievance Officer Contact Information",
            "description": "The Privacy Policy does not explicitly publish the name or email "
                           "of a designated Data Protection Officer / Grievance Officer.",
            "evidence_snippet": "Privacy Policy text lacks DPO contact details.",
            "remediation_suggestion": "Publish the designated DPO's business email and grievance "
                                     "redressal mechanism under Section 8(9).",
        })

    # Check Multi-lingual notice availability (DPDP Act Sec 5(3), Rule 3)
    if not gov_data["multilingual_support"]:
        grounding = match_statute_clause("Notice in Eighth Schedule languages")
        findings.append({
            "audit_id": audit_id,
            "agent_role": "policy_agent",
            "act_section": grounding["act_section"],
            "rules_clause": grounding["rules_clause"],
            "severity": "MEDIUM",
            "title": "Notice Not Readily Accessible in Eighth Schedule Languages",
            "description": "Notice is published only in English without accessible options in "
                           "the 22 Eighth Schedule languages specified in the Constitution.",
            "evidence_snippet": "Document is available only in English; no multi-lingual selector.",
            "remediation_suggestion": "Provide notice translation in Eighth Schedule languages "
                                     "under Section 5(3) and Rule 3.",
        })

    # Check DPA Log Retention SLA (DPDP Rules 2025 Rule 6(1)(e) & Rule 8(3))
    ret_days = gov_data["dpa_terms"]["log_retention_days"]
    if ret_days < 365:
        grounding = match_statute_clause("Maintain security logs for 1 year Rule 6(1)(e)")
        findings.append({
            "audit_id": audit_id,
            "agent_role": "policy_agent",
            "act_section": grounding["act_section"],
            "rules_clause": grounding["rules_clause"],
            "severity": "CRITICAL",
            "title": f"Sub-Statutory DPA Log Retention ({ret_days} days < 1 Year)",
            "description": f"Vendor DPA specifies {ret_days} days log retention. "
                           "DPDP Rules require a minimum of 1 year security log retention.",
            "evidence_snippet": f"DPA clause: retain logs for {ret_days} days.",
            "remediation_suggestion": "Update Vendor DPA clause to mandate 365-day log retention "
                                     "per Rule 6(1)(e) and Rule 8(3).",
        })

    # Check DPA Erasure upon Termination (DPDP Act Sec 8(7)(b))
    if not gov_data["dpa_terms"]["erasure_upon_termination"]:
        grounding = match_statute_clause("Erasure of personal data upon contract completion")
        findings.append({
            "audit_id": audit_id,
            "agent_role": "policy_agent",
            "act_section": grounding["act_section"],
            "rules_clause": grounding["rules_clause"],
            "severity": "HIGH",
            "title": "Missing Mandatory Data Processor Erasure Clause in DPA",
            "description": "Vendor DPA does not mandate data processor to erase all personal data "
                           "upon contract completion or consent withdrawal.",
            "evidence_snippet": "DPA text missing explicit data processor erasure clause.",
            "remediation_suggestion": "Include mandatory erasure clause under Section 8(7)(b).",
        })

    # Formulate structured governance promises payload
    governance_promises = [{
        "data_categories": gov_data["data_categories"],
        "purposes": gov_data["purposes"],
        "dpo_published": gov_data["dpo_info"]["dpo_published"],
        "dpo_email": gov_data["dpo_info"]["email"],
        "multilingual_support": gov_data["multilingual_support"],
        "dpa_terms": gov_data["dpa_terms"],
    }]

    # 4. Emit GOVERNANCE_RULES_READY onto the Event Bus
    event_bus = get_event_bus()
    await event_bus.publish(
        "GOVERNANCE_RULES_READY",
        {
            "audit_id": audit_id,
            "organization_id": state.get("organization_id"),
            "governance_promises": governance_promises,
        },
    )

    logger.info(f"[policy_agent] Completed audit {audit_id}: {len(findings)} findings emitted")

    return {
        "governance_promises": governance_promises,
        "findings": findings,
    }
