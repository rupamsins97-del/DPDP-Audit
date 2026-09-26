import logging
from typing import Any
from uuid import uuid4

from apps.api.agents.state import AuditContextState
from apps.api.tools.code_scanner import scan_codebase_for_violations
from apps.api.tools.event_bus import get_event_bus
from apps.api.tools.git_cloner import ephemeral_clone
from apps.api.tools.patch_generator import create_code_patch_for_violation

logger = logging.getLogger(__name__)


async def backend_agent_node(state: AuditContextState) -> dict[str, Any]:
    """Backend Agent: performs static SAST and AST analysis with ephemeral repo cloning."""
    audit_id = state.get("audit_id", "unknown-audit")
    repo_url = state.get("repository_url")
    event_bus = get_event_bus()

    repo_label = repo_url or "Local Sandbox"
    logger.info(f"[backend_agent] Initiating backend codebase audit for {audit_id} ({repo_label})")

    await event_bus.publish(
        "TELEMETRY_LOG",
        {
            "audit_id": audit_id,
            "agent_role": "backend_agent",
            "message": f"Cloning and initializing static scan for {repo_url or 'default'}...",
        },
    )

    findings: list[dict[str, Any]] = []
    generated_patches: list[dict[str, Any]] = []

    # Strict Invariant 2: Clone repository in ephemeral RAM sandbox with guaranteed cleanup
    with ephemeral_clone(repo_url) as sandbox_dir:
        violations = scan_codebase_for_violations(sandbox_dir)

        for v in violations:
            f_id = str(uuid4())
            file_name = v.get("file_path", "")
            line_num = v.get("line_number", 1)
            v_type = v.get("violation_type", "VIOLATION")

            # Telemetry narration matching master prompt style
            await event_bus.publish(
                "TELEMETRY_LOG",
                {
                    "audit_id": audit_id,
                    "agent_role": "backend_agent",
                    "message": f"Scanning {file_name}... Found {v_type} on Line {line_num}",
                },
            )

            # Build grounded finding (Invariant 3)
            finding = {
                "finding_id": f_id,
                "audit_id": audit_id,
                "agent_role": "backend_agent",
                "act_section": v.get("act_section", "DPDP Act Sec 8(5)"),
                "rules_clause": v.get("rules_clause", "DPDP Rules 2025 Rule 6"),
                "severity": v.get("severity", "HIGH"),
                "title": v.get("title", f"Code violation in {file_name}"),
                "description": v.get("description", ""),
                "evidence_snippet": v.get("evidence_snippet", ""),
                "remediation_suggestion": v.get("remediation_suggestion", ""),
            }
            findings.append(finding)

            # Generate Unified Diff patch for PII logging violations
            if v.get("violation_type") == "PLAINTEXT_PII_LOGGING":
                patch = create_code_patch_for_violation(v, finding_id=f_id)
                generated_patches.append(patch)

                await event_bus.publish(
                    "TELEMETRY_LOG",
                    {
                        "audit_id": audit_id,
                        "agent_role": "backend_agent",
                        "message": (
                            f"Generated patch for {file_name}:{line_num} "
                            "(status: PENDING_REVIEW)"
                        ),
                    },
                )

    count_findings = len(findings)
    count_patches = len(generated_patches)
    logger.info(
        f"[backend_agent] Completed {audit_id}: {count_findings} findings, {count_patches} patches"
    )

    return {
        "findings": findings,
        "generated_patches": generated_patches,
    }
