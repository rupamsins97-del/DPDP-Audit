import logging
import urllib.parse
from typing import Any

from apps.api.tools.axtree_parser import audit_axtree_consent_ui
from apps.api.tools.scrapfly_client import detect_anti_bot_protection

logger = logging.getLogger(__name__)

# Known third-party tracking, analytics, and advertising domains
KNOWN_TRACKER_DOMAINS: dict[str, str] = {
    "connect.facebook.net": "Meta Pixel",
    "pixel.facebook.com": "Meta Pixel",
    "facebook.com/tr": "Meta Pixel",
    "google-analytics.com": "Google Analytics",
    "googletagmanager.com": "Google Tag Manager",
    "doubleclick.net": "Google DoubleClick",
    "googleadservices.com": "Google AdServices",
    "analytics.tiktok.com": "TikTok Pixel",
    "byteoversea.com": "ByteDance Tracker",
    "clarity.ms": "Microsoft Clarity",
    "c.clarity.ms": "Microsoft Clarity",
    "hotjar.com": "Hotjar",
    "static.hotjar.com": "Hotjar",
    "api.mixpanel.com": "Mixpanel",
    "mixpanel.com": "Mixpanel",
    "api.segment.io": "Segment",
    "segment.com": "Segment",
    "api.amplitude.com": "Amplitude",
    "criteo.net": "Criteo",
    "criteo.com": "Criteo",
    "taboola.com": "Taboola",
    "outbrain.com": "Outbrain",
    "appsflyer.com": "AppsFlyer",
}


def is_tracker_domain(
    url: str, declared_trackers: list[str] | None = None
) -> tuple[bool, str | None]:
    """Determines whether a requested URL corresponds to a known or declared tracker domain."""
    try:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.lower()
        full_dest = f"{host}{path}"
    except Exception:
        return False, None

    # Check known domain catalog
    for domain, name in KNOWN_TRACKER_DOMAINS.items():
        if domain in host or domain in full_dest:
            return True, name

    # Check against declared trackers from governance promises
    if declared_trackers:
        for declared in declared_trackers:
            clean_dec = declared.lower().replace(" ", "")
            clean_host = host.replace(".", "")
            if clean_dec in clean_host:
                return True, declared

    return False, None


def evaluate_withdrawal_parity(
    steps_to_give: int,
    steps_to_withdraw: int,
    withdraw_evidence: str | None = None,
) -> list[dict[str, Any]]:
    """Evaluates consent withdrawal step parity against Rule 3(c)(i).

    Withdrawing consent must be as effortless and frictionless as giving consent.
    """
    findings: list[dict[str, Any]] = []

    if steps_to_withdraw > steps_to_give:
        findings.append(
            {
                "agent_role": "frontend_agent",
                "act_section": "DPDP Act Sec 6(4)",
                "rules_clause": "DPDP Rules 2025 Rule 3(c)(i)",
                "severity": "HIGH" if (steps_to_withdraw - steps_to_give) >= 2 else "MEDIUM",
                "title": "Consent Withdrawal Parity Asymmetry",
                "description": (
                    f"Withdrawing consent requires {steps_to_withdraw} user actions/steps, "
                    f"whereas granting consent required only {steps_to_give} action(s). "
                    "DPDP Section 6(4) and Rule 3(c)(i) mandate that the ease of revoking consent "
                    "must be commensurate with the ease of giving consent."
                ),
                "evidence_snippet": (
                    withdraw_evidence
                    or f"Steps to Give: {steps_to_give} | Steps to Withdraw: {steps_to_withdraw}"
                ),
                "remediation_suggestion": (
                    "Provide a direct 1-click 'Revoke All Consent' or persistent 'Manage Cookies' "
                    "control accessible across all web pages without deep navigation."
                ),
            }
        )

    return findings


async def audit_web_frontend(
    target_url: str,
    governance_promises: dict[str, Any] | None = None,
    session_headers: dict[str, str] | None = None,
    simulated_pre_consent_requests: list[str] | None = None,
    simulated_axtree: dict[str, Any] | None = None,
    simulated_steps_to_give: int = 1,
    simulated_steps_to_withdraw: int = 1,
) -> list[dict[str, Any]]:
    """Executes a full 360° frontend compliance audit (FR-2.1 – FR-2.4).

    Steps:
    1. Anti-bot protection detection (FR-2.4).
    2. Pre-consent CDP network interception (FR-2.1).
    3. AXTree consent banner & checkbox unbundling audit (FR-2.2).
    4. Consent withdrawal parity verification (FR-2.3).
    """
    findings: list[dict[str, Any]] = []
    promises = governance_promises or {}
    declared_trackers = promises.get("declared_trackers", [])
    supported_languages = promises.get("supported_languages", [])

    # 1. Inspect Anti-Bot Protection Headers (FR-2.4)
    is_protected, bot_provider = detect_anti_bot_protection(session_headers or {})
    if is_protected:
        logger.info(
            f"[frontend_agent] Target {target_url} protected by {bot_provider}. Routing Scrapfly."
        )

    # 2. Pre-Consent Network Interception (FR-2.1)
    pre_consent_urls = simulated_pre_consent_requests or []
    for req_url in pre_consent_urls:
        is_tracker, tracker_name = is_tracker_domain(req_url, declared_trackers=declared_trackers)
        if is_tracker:
            findings.append(
                {
                    "agent_role": "frontend_agent",
                    "act_section": "DPDP Act Sec 6(1)",
                    "rules_clause": "DPDP Rules 2025 Rule 3(2)",
                    "severity": "CRITICAL",
                    "title": f"Pre-Consent Third-Party Tracker Fired: {tracker_name or 'Tracker'}",
                    "description": (
                        f"Network request sent to tracker '{req_url}' before affirmative "
                        "user consent. DPDP Section 6(1) strictly prohibits initiating "
                        "tracking or data processing prior to unambiguous consent."
                    ),
                    "evidence_snippet": f"Pre-consent request: GET {req_url}",
                    "remediation_suggestion": (
                        "Block and defer execution of all third-party analytics and tracking "
                        "pixels until the user explicitly clicks 'Accept' or confirms consent."
                    ),
                }
            )

    # 3. Accessibility Tree (AXTree) Consent UI Audit (FR-2.2)
    if simulated_axtree:
        axtree_findings = audit_axtree_consent_ui(
            simulated_axtree, supported_languages=supported_languages
        )
        findings.extend(axtree_findings)

    # 4. Consent Withdrawal Parity Evaluation (FR-2.3)
    parity_findings = evaluate_withdrawal_parity(
        steps_to_give=simulated_steps_to_give,
        steps_to_withdraw=simulated_steps_to_withdraw,
    )
    findings.extend(parity_findings)

    return findings
