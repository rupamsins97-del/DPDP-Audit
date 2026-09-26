import asyncio
from typing import Any
from uuid import uuid4

import pytest
from apps.api.agents.frontend_agent import frontend_agent_node
from apps.api.agents.state import AuditContextState
from apps.api.tools.axtree_parser import audit_axtree_consent_ui, flatten_axtree
from apps.api.tools.browser_scanner import (
    audit_web_frontend,
    evaluate_withdrawal_parity,
    is_tracker_domain,
)
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.scrapfly_client import detect_anti_bot_protection, get_scrapfly_unblocker_url


def test_is_tracker_domain_identification() -> None:
    """Detects standard tracker domains (Meta Pixel, Google Analytics, ByteDance)."""
    meta_url = "https://connect.facebook.net/en_US/fbevents.js"
    is_meta, meta_name = is_tracker_domain(meta_url)
    assert is_meta is True
    assert meta_name == "Meta Pixel"

    ga_url = "https://www.google-analytics.com/analytics.js"
    is_ga, ga_name = is_tracker_domain(ga_url)
    assert is_ga is True
    assert ga_name == "Google Analytics"

    custom_url = "https://custom-analytics.mycompany.com/track"
    is_custom, custom_name = is_tracker_domain(
        custom_url, declared_trackers=["custom-analytics"]
    )
    assert is_custom is True
    assert custom_name == "custom-analytics"

    safe_url = "https://cdn.example.com/assets/logo.png"
    is_safe, _ = is_tracker_domain(safe_url)
    assert is_safe is False


@pytest.mark.asyncio
async def test_pre_consent_tracker_flagged_critical() -> None:
    """Pre-consent network request to tracker domain is flagged CRITICAL under Section 6(1)."""
    pre_consent_urls = [
        "https://connect.facebook.net/en_US/fbevents.js",
        "https://www.google-analytics.com/collect?v=2",
        "https://cdn.example.com/main.css",
    ]

    findings = await audit_web_frontend(
        target_url="https://example.com",
        simulated_pre_consent_requests=pre_consent_urls,
    )

    # 2 trackers should be flagged as CRITICAL
    tracker_findings = [f for f in findings if f["severity"] == "CRITICAL"]
    assert len(tracker_findings) == 2

    first = tracker_findings[0]
    assert first["agent_role"] == "frontend_agent"
    assert first["act_section"] == "DPDP Act Sec 6(1)"
    assert "Rule 3(2)" in first["rules_clause"]
    assert "Pre-Consent Third-Party Tracker" in first["title"]
    evidence = first["evidence_snippet"]
    assert "facebook.net" in evidence or "google-analytics" in evidence


def test_axtree_pre_checked_consent_box_flagged() -> None:
    """AXTree with pre-checked non-essential checkbox flags violation (FR-2.2)."""
    mock_axtree: dict[str, Any] = {
        "role": "dialog",
        "name": "Privacy and Cookie Preferences",
        "children": [
            {
                "role": "checkbox",
                "name": "Strictly Necessary Cookies",
                "checked": True,
                "disabled": True,
            },
            {
                "role": "checkbox",
                "name": "Marketing & Advertising Pixels",
                "checked": True,  # Non-compliant: pre-checked!
            },
            {
                "role": "checkbox",
                "name": "Analytics and Performance Measurement",
                "checked": False,
            },
            {
                "role": "button",
                "name": "Save Preferences",
            },
        ],
    }

    # Verify flatten_axtree helper
    flat = flatten_axtree(mock_axtree)
    assert len(flat) == 5  # Dialog + 3 Checkboxes + 1 Button

    findings = audit_axtree_consent_ui(mock_axtree)
    assert len(findings) == 1
    assert findings[0]["act_section"] == "DPDP Act Sec 6(1)"
    assert "Rule 3(1)" in findings[0]["rules_clause"]
    assert findings[0]["severity"] == "HIGH"
    assert "Pre-Checked Consent Option Detected" in findings[0]["title"]
    assert "Marketing & Advertising Pixels" in findings[0]["title"]


def test_withdrawal_parity_asymmetry_flagged() -> None:
    """Withdrawal parity flags when revoking requires more actions than giving consent (FR-2.3)."""
    # 1 step to give consent vs 4 steps to withdraw consent
    findings = evaluate_withdrawal_parity(steps_to_give=1, steps_to_withdraw=4)

    assert len(findings) == 1
    assert findings[0]["act_section"] == "DPDP Act Sec 6(4)"
    assert "Rule 3(c)(i)" in findings[0]["rules_clause"]
    assert findings[0]["severity"] == "HIGH"
    assert "Withdrawal Parity Asymmetry" in findings[0]["title"]
    assert "4 user actions/steps" in findings[0]["description"]

    # Symmetric case: 1 step give, 1 step withdraw -> 0 findings
    symmetric_findings = evaluate_withdrawal_parity(steps_to_give=1, steps_to_withdraw=1)
    assert len(symmetric_findings) == 0


def test_anti_bot_detection_and_scrapfly_routing() -> None:
    """Anti-bot detection inspects Cloudflare/DataDome/Akamai headers (FR-2.4)."""
    cf_headers = {"cf-ray": "8937bc901a2c3-BOM", "server": "cloudflare"}
    is_protected, provider = detect_anti_bot_protection(cf_headers)
    assert is_protected is True
    assert provider == "Cloudflare"

    datadome_headers = {"server": "DataDome", "x-datadome-response": "403"}
    is_dd, dd_provider = detect_anti_bot_protection(datadome_headers)
    assert is_dd is True
    assert dd_provider == "DataDome"

    akamai_headers = {"x-akamai-transformed": "9 - 0 pmb=mRUM,1"}
    is_ak, ak_provider = detect_anti_bot_protection(akamai_headers)
    assert is_ak is True
    assert ak_provider == "Akamai"

    unprotected_headers = {"server": "nginx", "content-type": "text/html"}
    is_unprot, _ = detect_anti_bot_protection(unprotected_headers)
    assert is_unprot is False

    scrapfly_url = get_scrapfly_unblocker_url("https://protected-portal.in/login", api_key="KEY123")
    assert "https://api.scrapfly.io/scrape" in scrapfly_url
    assert "asp=true" in scrapfly_url
    assert "render_js=true" in scrapfly_url
    assert "country=in" in scrapfly_url


@pytest.mark.asyncio
async def test_frontend_agent_node_runs_and_emits_telemetry() -> None:
    """frontend_agent_node executes cleanly, emits telemetry, and returns structured findings."""
    audit_id = str(uuid4())
    org_id = str(uuid4())
    event_bus = get_event_bus()

    telemetry_logs = []

    async def log_subscriber():
        async for msg in event_bus.subscribe("TELEMETRY_LOG"):
            if msg.get("payload", {}).get("audit_id") == audit_id:
                telemetry_logs.append(msg["payload"]["message"])
                if len(telemetry_logs) >= 3:
                    break

    task = asyncio.create_task(log_subscriber())
    await asyncio.sleep(0.01)

    state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Web Audit Test",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "governance_promises": [{"declared_trackers": ["Meta Pixel"]}],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    result = await frontend_agent_node(state)
    await asyncio.sleep(0.05)
    task.cancel()

    assert "findings" in result
    assert isinstance(result["findings"], list)
    assert len(telemetry_logs) >= 2
    assert any("Intercepting network" in log for log in telemetry_logs)
