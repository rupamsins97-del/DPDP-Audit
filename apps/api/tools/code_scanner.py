import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Extensions to scan for application code
SCANNABLE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".sql"}

# Patterns for sensitive variables and PII keywords
PII_REGEX = re.compile(
    r"(?i)\b(aadhaar|pan|email|phone|mobile|password|passcode|secret|ssn|"
    r"credit_card|bank_account|user_email|user_phone)\b"
)

# Logger invocation patterns across supported languages
LOGGER_PATTERNS = [
    # Python logger/print
    re.compile(
        r"(logger\.(info|debug|warning|error|exception)|logging\.(info|debug|warning|error)|print)"
        r"\s*\((.*)\)",
        re.IGNORECASE,
    ),
    # JS/TS console / logger
    re.compile(
        r"(console\.(log|info|warn|error)|logger\.(info|debug|warn|error)|"
        r"winston\.(info|debug|error))\s*\((.*)\)",
        re.IGNORECASE,
    ),
    # Go logger
    re.compile(
        r"(log\.(Printf|Println|Print)|fmt\.(Printf|Println)|logger\.(Info|Debug|Warn|Error))"
        r"\s*\((.*)\)",
        re.IGNORECASE,
    ),
    # Java logger
    re.compile(
        r"(logger\.(info|debug|warn|error)|System\.out\.(println|print)|log\.(info|debug))"
        r"\s*\((.*)\)",
        re.IGNORECASE,
    ),
]

# Unencrypted DB field patterns
DB_FIELD_PATTERN = re.compile(
    r"(?i)(aadhaar|pan_number|bank_account|ssn)\s*=\s*Column\((String|Text)[^\)]*\)"
)

IGNORED_DIRECTORIES = {
    "node_modules", "vendor", ".git", ".next", "dist", "build", "__pycache__", "assets"
}


def is_ignored(rel_path: str) -> bool:
    """Checks if a relative path matches common ignore directories to keep memory < 2GB."""
    parts = Path(rel_path).parts
    return any(p in IGNORED_DIRECTORIES for p in parts)


def scan_codebase_for_violations(repo_dir: str) -> list[dict[str, Any]]:
    """Performs static AST/heuristic scanning on the ephemeral repository for DPDP violations."""
    violations: list[dict[str, Any]] = []

    for root, dirs, files in os.walk(repo_dir):
        # Prune ignored directories in-place for fast traversal
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in SCANNABLE_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_dir).replace("\\", "/")

            if is_ignored(rel_path):
                continue

            try:
                with open(full_path, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception as e:
                logger.warning(f"Could not read {rel_path}: {e}")
                continue

            # Scan line-by-line
            has_retention_timestamp = False
            is_model_file = any(
                k in rel_path for k in ("models", "entities", "schema")
            ) or "user" in file.lower()

            for idx, line in enumerate(lines, start=1):
                stripped = line.strip()

                # Check timestamp for retention models
                if is_model_file and any(
                    ts in stripped.lower()
                    for ts in ("created_at", "updated_at", "deleted_at", "retention_timer")
                ):
                    has_retention_timestamp = True

                # 1. Plaintext PII Logging (Section 8(5))
                for log_pat in LOGGER_PATTERNS:
                    if log_pat.search(stripped) and PII_REGEX.search(stripped):
                        violations.append({
                            "file_path": rel_path,
                            "line_number": idx,
                            "line_content": stripped,
                            "violation_type": "PLAINTEXT_PII_LOGGING",
                            "act_section": "DPDP Act Sec 8(5)",
                            "rules_clause": "DPDP Rules 2025 Rule 6",
                            "severity": "HIGH",
                            "title": f"Plaintext PII Logging in {file} (Line {idx})",
                            "description": (
                                f"Unmasked personal identifier logged in {rel_path}:{idx}. "
                                "DPDP Act Section 8(5) mandates reasonable security safeguards."
                            ),
                            "evidence_snippet": f"{rel_path}:{idx} -> {stripped}",
                            "remediation_suggestion": (
                                "Mask or hash the PII variable using SHA-256 / "
                                "pseudonymization before logging."
                            ),
                        })
                        break

                # 2. Unencrypted Sensitive DB Field (Section 8(5))
                if is_model_file and DB_FIELD_PATTERN.search(stripped):
                    violations.append({
                        "file_path": rel_path,
                        "line_number": idx,
                        "line_content": stripped,
                        "violation_type": "UNENCRYPTED_DB_FIELD",
                        "act_section": "DPDP Act Sec 8(5)",
                        "rules_clause": "DPDP Rules 2025 Rule 6",
                        "severity": "HIGH",
                        "title": f"Unencrypted Sensitive Column in {file} (Line {idx})",
                        "description": (
                            "Government identity/financial field defined without field-level "
                            f"encryption directive in {rel_path}:{idx}."
                        ),
                        "evidence_snippet": f"{rel_path}:{idx} -> {stripped}",
                        "remediation_suggestion": (
                            "Apply EncryptedType or KMS envelope encryption on sensitive column."
                        ),
                    })

            # 3. Missing Retention / Erasure Logic (Section 8(7))
            if is_model_file and not has_retention_timestamp and len(lines) > 5:
                violations.append({
                    "file_path": rel_path,
                    "line_number": 1,
                    "line_content": lines[0].strip() if lines else "",
                    "violation_type": "MISSING_RETENTION_TRIGGER",
                    "act_section": "DPDP Act Sec 8(7)",
                    "rules_clause": "DPDP Rules 2025 Rule 8",
                    "severity": "MEDIUM",
                    "title": f"Missing Retention/Erasure Timestamp in {file}",
                    "description": (
                        f"Entity model in {rel_path} lacks created_at/deleted_at timestamps "
                        "necessary for automated statutory data retention and erasure."
                    ),
                    "evidence_snippet": f"{rel_path} model definition lacks lifecycle timestamps.",
                    "remediation_suggestion": (
                        "Add created_at, updated_at, and deleted_at timestamps and "
                        "automated purge trigger."
                    ),
                })

    return violations
