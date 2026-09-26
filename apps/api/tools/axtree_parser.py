import logging
from typing import Any

logger = logging.getLogger(__name__)

# Non-essential tracking categories that MUST NOT be pre-checked
NON_ESSENTIAL_CATEGORIES = (
    "analytics",
    "analytic",
    "marketing",
    "advertising",
    "advertisement",
    "tracker",
    "tracking",
    "personalization",
    "profiling",
    "measurement",
    "social media",
    "performance",
    "targeting",
)

# Eighth Schedule recognized Indian languages
EIGHTH_SCHEDULE_LANGUAGES = {
    "hi": "Hindi",
    "bn": "Bengali",
    "te": "Telugu",
    "mr": "Marathi",
    "ta": "Tamil",
    "ur": "Urdu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "pa": "Punjabi",
    "as": "Assamese",
    "ma": "Maithili",
    "sa": "Sanskrit",
}


def flatten_axtree(node: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recursively flattens an Accessibility Tree (AXTree) snapshot into a node list."""
    flattened: list[dict[str, Any]] = []

    if isinstance(node, list):
        for item in node:
            flattened.extend(flattenaxtree_helper(item))
        return flattened

    if not isinstance(node, dict):
        return flattened

    # Shallow copy node without children for flat representation
    node_copy = {k: v for k, v in node.items() if k != "children"}
    flattened.append(node_copy)

    children = node.get("children", [])
    if isinstance(children, list):
        for child in children:
            flattened.extend(flatten_axtree(child))

    return flattened


def flattenaxtree_helper(item: Any) -> list[dict[str, Any]]:
    return flatten_axtree(item)


def audit_axtree_consent_ui(
    axtree_snapshot: dict[str, Any] | list[dict[str, Any]],
    supported_languages: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Audits accessibility tree nodes for DPDP Section 6(1) unbundled consent compliance.

    Verifies:
    1. No pre-checked checkboxes for non-essential cookies/trackers (Rule 3(1)).
    2. Granular, unbundled choices rather than forced all-or-nothing consent.
    3. Multi-lingual Eighth Schedule language support if declared in governance promises.
    """
    findings: list[dict[str, Any]] = []
    flat_nodes = flatten_axtree(axtree_snapshot)

    # 1. Search for checkboxes / switches
    checkbox_nodes = [
        n for n in flat_nodes if n.get("role") in ("checkbox", "switch", "menuitemcheckbox")
    ]

    for cb in checkbox_nodes:
        name = str(cb.get("name", "")).strip()
        name_lower = name.lower()
        is_checked = cb.get("checked") is True or cb.get("checked") == "true"

        # Check if non-essential category is pre-checked
        is_non_essential = any(cat in name_lower for cat in NON_ESSENTIAL_CATEGORIES)
        is_explicitly_necessary = any(
            ess in name_lower for ess in ("necessary", "essential", "strictly necessary")
        )

        if is_checked and is_non_essential and not is_explicitly_necessary:
            findings.append(
                {
                    "agent_role": "frontend_agent",
                    "act_section": "DPDP Act Sec 6(1)",
                    "rules_clause": "DPDP Rules 2025 Rule 3(1)",
                    "severity": "HIGH",
                    "title": f"Pre-Checked Consent Option Detected: '{name}'",
                    "description": (
                        f"Accessibility node '{name}' (role: {cb.get('role')}) was found "
                        "pre-checked by default for non-essential processing. DPDP Section 6(1) "
                        "and Rule 3(1) require affirmative, unbundled, and un-ticked opt-in."
                    ),
                    "evidence_snippet": (
                        f"AXTree Node: role={cb.get('role')}, name='{name}', "
                        f"checked={cb.get('checked')}"
                    ),
                    "remediation_suggestion": (
                        "Set default state of all non-essential consent checkboxes to unchecked "
                        "and require unambiguous affirmative user action."
                    ),
                }
            )

    # 2. Check for Bundled All-or-Nothing Consent
    buttons = [n for n in flat_nodes if n.get("role") in ("button", "link")]
    button_names = [str(b.get("name", "")).lower() for b in buttons]

    has_accept_all = any("accept all" in name or "agree to all" in name for name in button_names)
    has_customization = (
        any(
            cust in name
            for cust in ("manage", "preferences", "customize", "settings", "cookie settings")
            for name in button_names
        )
        or len(checkbox_nodes) > 1
    )

    if has_accept_all and not has_customization and len(checkbox_nodes) == 0:
        findings.append(
            {
                "agent_role": "frontend_agent",
                "act_section": "DPDP Act Sec 6(1)",
                "rules_clause": "DPDP Rules 2025 Rule 3(1)",
                "severity": "MEDIUM",
                "title": "Bundled All-or-Nothing Consent Notice",
                "description": (
                    "Consent prompt provides an 'Accept All' action without granular category "
                    "controls or customization preferences. DPDP Section 6(1) mandates unbundled "
                    "consent options itemised by specific purpose."
                ),
                "evidence_snippet": (
                    f"Available AXTree actions: {[b.get('name') for b in buttons[:5]]}"
                ),
                "remediation_suggestion": (
                    "Provide unbundled itemised consent checkboxes enabling users to opt into "
                    "distinct processing purposes independently."
                ),
            }
        )

    # 3. Check for Multi-lingual Eighth Schedule Language Availability
    if supported_languages:
        available_text = " ".join([str(n.get("name", "")) for n in flat_nodes]).lower()
        missing_langs = []
        for lang_code in supported_languages:
            lang_name = EIGHTH_SCHEDULE_LANGUAGES.get(lang_code.lower(), lang_code).lower()
            if lang_name not in available_text and lang_code.lower() not in available_text:
                missing_langs.append(lang_code)

        if missing_langs and len(missing_langs) == len(supported_languages):
            findings.append(
                {
                    "agent_role": "frontend_agent",
                    "act_section": "DPDP Act Sec 5(3)",
                    "rules_clause": "DPDP Rules 2025 Rule 3(2)",
                    "severity": "LOW",
                    "title": "Missing Multi-Lingual Eighth Schedule Notice Selector",
                    "description": (
                        f"Governance policy declared multi-lingual support for "
                        f"{supported_languages}, but AXTree inspection did not detect accessible "
                        "language selectors or translations in Eighth Schedule languages."
                    ),
                    "evidence_snippet": f"Declared languages: {supported_languages}",
                    "remediation_suggestion": (
                        "Provide accessible multi-lingual toggles in consent banners supporting "
                        "the declared Eighth Schedule languages."
                    ),
                }
            )

    return findings
