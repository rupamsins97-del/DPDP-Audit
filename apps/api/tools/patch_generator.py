import logging
import re
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

SENSITIVE_PII_KEYWORDS = (
    "aadhaar", "pan", "email", "phone", "password", "mobile", "ssn", "card", "bank"
)


def generate_unified_diff(
    file_path: str,
    original_line: str,
    patched_line: str,
    line_number: int = 1,
) -> str:
    """Generates standard Unified Diff format for a single line replacement."""
    clean_path = file_path.replace("\\", "/")
    return (
        f"--- a/{clean_path}\n"
        f"+++ b/{clean_path}\n"
        f"@@ -{line_number},1 +{line_number},1 @@\n"
        f"- {original_line}\n"
        f"+ {patched_line}\n"
    )


def remediate_pii_logging_line(original_line: str) -> str:
    """Generates a remediated logger statement that masks or hashes sensitive PII variables."""
    patched = original_line

    # Python f-string or formatting masking
    # E.g. {user_email} -> {hash_pii(user_email)} or {mask_aadhaar(aadhaar_number)}
    if "{" in patched and "}" in patched:
        def _replace_fstring(m):
            var_name = m.group(1).strip()
            if any(k in var_name.lower() for k in SENSITIVE_PII_KEYWORDS):
                return f"{{hash_pii({var_name})}}"
            return m.group(0)

        patched = re.sub(r"\{([a-zA-Z0-9_\.]+)\}", _replace_fstring, patched)
    else:
        # Direct argument or template string
        # E.g. console.log(`... ${email} ...`)
        if "${" in patched:
            def _replace_js(m):
                var_name = m.group(1).strip()
                if any(k in var_name.lower() for k in SENSITIVE_PII_KEYWORDS):
                    return f"${{maskPII({var_name})}}"
                return m.group(0)
            patched = re.sub(r"\$\{([a-zA-Z0-9_\.]+)\}", _replace_js, patched)

    # If no replacement was triggered, append pseudonymization helper
    if patched == original_line:
        patched = re.sub(
            r"(aadhaar|pan|email|phone|password)",
            r"masked_\1",
            patched,
            flags=re.IGNORECASE,
        )

    return patched


def create_code_patch_for_violation(
    violation: dict[str, Any],
    finding_id: str | None = None,
) -> dict[str, Any]:
    """Creates a Unified Diff remediation patch with PENDING_REVIEW status for a code violation."""
    file_path = violation.get("file_path", "app/main.py")
    line_num = violation.get("line_number", 1)
    original_line = violation.get("line_content", "")

    patched_line = remediate_pii_logging_line(original_line)
    diff_content = generate_unified_diff(file_path, original_line, patched_line, line_num)

    f_id = finding_id or str(uuid4())
    patch_id = str(uuid4())

    return {
        "patch_id": patch_id,
        "finding_id": f_id,
        "file_path": file_path,
        "original_code": original_line,
        "patched_code": patched_line,
        "diff_content": diff_content,
        "status": "PENDING_REVIEW",  # Strictly PENDING_REVIEW per Verification Item 5
    }
