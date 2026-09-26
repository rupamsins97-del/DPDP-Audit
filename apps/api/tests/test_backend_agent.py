import os
import tempfile
from uuid import uuid4

import pytest
from apps.api.agents.backend_agent import backend_agent_node
from apps.api.agents.state import AuditContextState
from apps.api.tools.code_scanner import scan_codebase_for_violations
from apps.api.tools.git_cloner import ephemeral_clone
from apps.api.tools.patch_generator import (
    create_code_patch_for_violation,
    generate_unified_diff,
    remediate_pii_logging_line,
)


def test_ephemeral_clone_purges_on_success() -> None:
    """Verifies that the ephemeral clone sandbox is deleted on normal exit (Invariant 2)."""
    sandbox_path = None
    with ephemeral_clone(None) as temp_dir:
        sandbox_path = temp_dir
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)

    assert sandbox_path is not None
    assert not os.path.exists(sandbox_path), "Tmpfs sandbox must be purged after context exit"


def test_ephemeral_clone_purges_on_forced_exception() -> None:
    """Verifies that the ephemeral clone sandbox is deleted on exception (Invariant 2)."""
    sandbox_path = None
    with pytest.raises(RuntimeError, match="Forced scan crash"):
        with ephemeral_clone(None) as temp_dir:
            sandbox_path = temp_dir
            assert os.path.exists(temp_dir)
            raise RuntimeError("Forced scan crash")

    assert sandbox_path is not None
    assert not os.path.exists(sandbox_path), "Tmpfs must be purged on unhandled exception"


def test_plaintext_pii_logging_flagged_with_section_8_5() -> None:
    """Verifies that known plaintext PII log lines are detected with DPDP Section 8(5)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = os.path.join(tmp_dir, "test_controller.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(
                "import logging\n"
                "logger = logging.getLogger(__name__)\n"
                "def authenticate(email, password):\n"
                "    logger.info(f'User login with email: {email} and pass: {password}')\n"
            )

        violations = scan_codebase_for_violations(tmp_dir)
        assert len(violations) >= 1
        v = violations[0]
        assert "Sec 8(5)" in v["act_section"] or "Section 8(5)" in v["act_section"]
        assert v["violation_type"] == "PLAINTEXT_PII_LOGGING"
        assert v["severity"] == "HIGH"


def test_patch_generation_and_unified_diff() -> None:
    """Verifies that generated .patch is valid Unified Diff and status is PENDING_REVIEW."""
    original_line = "logger.info(f'User details: {user_email}, phone: {user_phone}')"
    patched_line = remediate_pii_logging_line(original_line)

    assert "hash_pii(user_email)" in patched_line
    assert "hash_pii(user_phone)" in patched_line

    diff = generate_unified_diff("app/controllers/user.py", original_line, patched_line, 14)
    assert "--- a/app/controllers/user.py" in diff
    assert "+++ b/app/controllers/user.py" in diff
    assert "- logger.info" in diff
    assert "+ logger.info" in diff

    violation = {
        "file_path": "app/controllers/user.py",
        "line_number": 14,
        "line_content": original_line,
        "violation_type": "PLAINTEXT_PII_LOGGING",
    }
    patch = create_code_patch_for_violation(violation)
    assert patch["status"] == "PENDING_REVIEW"
    assert patch["file_path"] == "app/controllers/user.py"


@pytest.mark.asyncio
async def test_backend_agent_node_runs_and_generates_findings_and_patches() -> None:
    """Verifies backend_agent_node end to end with findings and patches."""
    audit_id = str(uuid4())
    org_id = str(uuid4())

    state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Backend SAST Test",
        "target_url": "https://example.com",
        "repository_url": None,
        "framework": "BOTH",
        "status": "IN_PROGRESS",
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    result = await backend_agent_node(state)

    assert len(result["findings"]) >= 2
    assert len(result["generated_patches"]) >= 1

    # Verify all generated patches have PENDING_REVIEW
    for patch in result["generated_patches"]:
        assert patch["status"] == "PENDING_REVIEW"
        assert patch["diff_content"].startswith("--- a/")

    # Verify findings are grounded
    for finding in result["findings"]:
        assert finding["act_section"] is not None
        assert finding["agent_role"] == "backend_agent"
