import logging
import os
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

# Common anti-bot signature headers and indicators
ANTI_BOT_SIGNATURES: dict[str, str] = {
    "cf-ray": "Cloudflare",
    "cf-mitigated": "Cloudflare",
    "cf-cache-status": "Cloudflare",
    "x-datadome": "DataDome",
    "x-datadome-response": "DataDome",
    "x-akamai-transformed": "Akamai",
    "x-akamai-session-info": "Akamai",
    "x-px": "PerimeterX / HUMAN",
    "x-sucuri-id": "Sucuri",
    "x-iinfo": "Imperva Incapsula",
}


def detect_anti_bot_protection(headers: dict[str, str]) -> tuple[bool, str | None]:
    """Inspects response headers to detect anti-bot protection mechanisms (FR-2.4).

    Returns (is_protected, provider_name).
    """
    normalized_headers = {k.lower(): v.lower() for k, v in headers.items()}

    # Check header keys
    for header_key, provider in ANTI_BOT_SIGNATURES.items():
        if header_key in normalized_headers:
            return True, provider

    # Check server header values
    server_header = normalized_headers.get("server", "")
    if "cloudflare" in server_header:
        return True, "Cloudflare"
    if "datadome" in server_header:
        return True, "DataDome"
    if "akamai" in server_header:
        return True, "Akamai"
    if "imperva" in server_header or "incapsula" in server_header:
        return True, "Imperva Incapsula"

    return False, None


def get_scrapfly_unblocker_url(
    target_url: str,
    api_key: str | None = None,
    render_js: bool = True,
    asp: bool = True,
) -> str:
    """Builds a Scrapfly Unblocker API proxy endpoint URL for bypassing anti-bot systems."""
    key = api_key or os.getenv("SCRAPFLY_API_KEY", "DEMO_KEY")
    encoded_url = urllib.parse.quote(target_url, safe="")
    base_endpoint = "https://api.scrapfly.io/scrape"

    params = [
        f"key={key}",
        f"url={encoded_url}",
        f"render_js={'true' if render_js else 'false'}",
        f"asp={'true' if asp else 'false'}",
        "country=in",
    ]

    return f"{base_endpoint}?{'&'.join(params)}"


def get_scrapfly_proxy_dict(api_key: str | None = None) -> dict[str, Any]:
    """Generates proxy config dictionary when routing CDP traffic through Scrapfly."""
    key = api_key or os.getenv("SCRAPFLY_API_KEY", "")
    if not key:
        return {}

    return {
        "server": "https://proxy.scrapfly.io:8080",
        "username": key,
        "password": "asp=true&render_js=true&country=in",
    }
