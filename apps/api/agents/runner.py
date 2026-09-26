import logging
from typing import Any

from apps.api.agents.graph import audit_graph
from apps.api.agents.state import AuditContextState
from supabase import Client

logger = logging.getLogger(__name__)


async def run_audit_pipeline(
    audit_id: str,
    organization_id: str,
    project_name: str,
    target_url: str,
    repository_url: str | None,
    framework: str,
    supabase: Client,
) -> dict[str, Any]:
    """Executes the compiled LangGraph workflow asynchronously in the background."""
    logger.info(f"Starting LangGraph audit pipeline for {audit_id}")

    initial_state: AuditContextState = {
        "audit_id": audit_id,
        "organization_id": organization_id,
        "project_name": project_name,
        "target_url": target_url,
        "repository_url": repository_url,
        "framework": framework,
        "status": "IN_PROGRESS",
        "governance_promises": [],
        "findings": [],
        "generated_patches": [],
        "compliance_score": None,
        "state_hash": None,
        "error": None,
    }

    try:
        final_state = await audit_graph.ainvoke(initial_state)

        # Update in-memory store
        from apps.api.routers.audits import (
            _IN_MEMORY_AUDITS,
            _IN_MEMORY_FINDINGS,
            _IN_MEMORY_PATCHES,
        )

        if audit_id in _IN_MEMORY_AUDITS:
            _IN_MEMORY_AUDITS[audit_id]["status"] = final_state.get("status", "COMPLETED")
            _IN_MEMORY_AUDITS[audit_id]["compliance_score"] = final_state.get("compliance_score", 100)
            _IN_MEMORY_AUDITS[audit_id]["state_hash"] = final_state.get("state_hash")

        import uuid
        from datetime import datetime, UTC
        now_str = datetime.now(UTC).isoformat()

        enriched_findings = []
        for f in final_state.get("findings", []):
            f_dict = f.copy() if isinstance(f, dict) else (f.model_dump() if hasattr(f, "model_dump") else dict(f))
            f_dict.setdefault("finding_id", str(uuid.uuid4()))
            f_dict.setdefault("audit_id", audit_id)
            f_dict.setdefault("created_at", now_str)
            enriched_findings.append(f_dict)
        _IN_MEMORY_FINDINGS[audit_id] = enriched_findings

        enriched_patches = []
        for p in final_state.get("generated_patches", []):
            p_dict = p.copy() if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else dict(p))
            p_dict.setdefault("patch_id", str(uuid.uuid4()))
            p_dict.setdefault("created_at", now_str)
            enriched_patches.append(p_dict)
        _IN_MEMORY_PATCHES[audit_id] = enriched_patches


        # Update Supabase audit record upon completion
        try:
            supabase.table("audits").update(
                {
                    "status": final_state.get("status", "COMPLETED"),
                    "compliance_score": final_state.get("compliance_score", 100),
                    "state_hash": final_state.get("state_hash"),
                }
            ).eq("audit_id", audit_id).execute()
        except Exception as db_err:
            logger.warning(f"Supabase update skipped/failed for audit {audit_id}: {db_err}")

        score = final_state.get("compliance_score")
        logger.info(f"LangGraph audit pipeline completed for {audit_id} with score {score}")
        return final_state
    except Exception as e:
        logger.error(f"LangGraph audit pipeline execution error for {audit_id}: {e}")
        try:
            supabase.table("audits").update({"status": "FAILED"}).eq("audit_id", audit_id).execute()
        except Exception as db_err:
            logger.error(f"Failed to update audit status to FAILED: {db_err}")
        raise

