import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from apps.api.agents.runner import run_audit_pipeline
from apps.api.auth import UserSession, get_current_user_session, get_supabase_client
from apps.api.schemas import (
    ApiResponse,
    AuditContextStateResponse,
    AuditResponse,
    CodePatchSchema,
    CreateAuditRequest,
    FindingSchema,
)
from apps.api.tools.event_bus import get_event_bus
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audits"])

_IN_MEMORY_AUDITS: dict[str, dict[str, Any]] = {}
_IN_MEMORY_FINDINGS: dict[str, list[dict[str, Any]]] = {}
_IN_MEMORY_PATCHES: dict[str, list[dict[str, Any]]] = {}


@router.post(
    "/audits",
    response_model=ApiResponse[dict[str, str]],
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/api/v1/audits",
    response_model=ApiResponse[dict[str, str]],
    status_code=status.HTTP_201_CREATED,
)
async def create_audit(
    request: CreateAuditRequest,
    background_tasks: BackgroundTasks,
    session: UserSession = Depends(get_current_user_session),
    supabase: Client = Depends(get_supabase_client),
) -> ApiResponse[dict[str, str]]:
    """Enqueues a new 360° compliance audit and returns immediately (Invariant 1)."""
    import uuid
    from datetime import datetime, UTC

    audit_id = str(uuid.uuid4())
    now_iso = datetime.now(UTC).isoformat()
    payload = {
        "audit_id": audit_id,
        "organization_id": session.organization_id,
        "project_name": request.project_name,
        "target_url": str(request.target_url),
        "repository_url": request.repository_url,
        "status": "IN_PROGRESS",
        "compliance_score": None,
        "state_hash": None,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # Store in memory store
    _IN_MEMORY_AUDITS[audit_id] = payload

    # Attempt inserting audit record into Supabase
    try:
        response = supabase.table("audits").insert(payload).execute()
        if response.data and len(response.data) > 0:
            audit_id = str(response.data[0]["audit_id"])
            _IN_MEMORY_AUDITS[audit_id] = response.data[0]
    except Exception as e:
        logger.warning(f"Supabase write bypassed/failed, using in-memory store for audit {audit_id}: {e}")

    # Enqueue LangGraph background task (non-blocking)
    background_tasks.add_task(
        run_audit_pipeline,
        audit_id=audit_id,
        organization_id=session.organization_id,
        project_name=request.project_name,
        target_url=str(request.target_url),
        repository_url=request.repository_url,
        framework=request.framework.value,
        supabase=supabase,
    )

    return ApiResponse(
        data={
            "audit_id": audit_id,
            "status": "IN_PROGRESS",
            "organization_id": session.organization_id,
        },
        error=None,
    )



@router.get(
    "/audits/{audit_id}",
    response_model=ApiResponse[AuditContextStateResponse],
)
@router.get(
    "/api/v1/audits/{audit_id}",
    response_model=ApiResponse[AuditContextStateResponse],
)
async def get_audit(
    audit_id: str,
    session: UserSession = Depends(get_current_user_session),
    supabase: Client = Depends(get_supabase_client),
) -> ApiResponse[AuditContextStateResponse]:
    """Retrieves an audit state snapshot scoped strictly to the authenticated organization."""
    try:
        audit_data: dict[str, Any] | None = None
        # Try fetching from Supabase
        try:
            audit_res = (
                supabase.table("audits")
                .select("*")
                .eq("audit_id", audit_id)
                .eq("organization_id", session.organization_id)
                .limit(1)
                .execute()
            )
            if audit_res.data and len(audit_res.data) > 0:
                audit_data = audit_res.data[0]
        except Exception:
            pass

        # Check in-memory store if not found in database
        if not audit_data:
            if audit_id in _IN_MEMORY_AUDITS and _IN_MEMORY_AUDITS[audit_id]["organization_id"] == session.organization_id:
                audit_data = _IN_MEMORY_AUDITS[audit_id]

        if not audit_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit '{audit_id}' not found or does not belong to your organization",
            )

        # Fetch findings
        findings: list[FindingSchema] = []
        try:
            findings_res = (
                supabase.table("audit_findings")
                .select("*")
                .eq("audit_id", audit_id)
                .order("created_at")
                .execute()
            )
            findings = [FindingSchema(**f) for f in (findings_res.data or [])]
        except Exception:
            pass

        if not findings and audit_id in _IN_MEMORY_FINDINGS:
            import uuid
            for f in _IN_MEMORY_FINDINGS[audit_id]:
                f_dict = f.copy() if isinstance(f, dict) else (f.model_dump() if hasattr(f, "model_dump") else dict(f))
                f_dict.setdefault("finding_id", str(uuid.uuid4()))
                f_dict.setdefault("audit_id", audit_id)
                f_dict.setdefault("created_at", str(audit_data.get("created_at", "")))
                findings.append(FindingSchema(**f_dict))

        # Fetch patches
        patches: list[CodePatchSchema] = []
        if findings:
            finding_ids = [f.finding_id for f in findings]
            try:
                patches_res = (
                    supabase.table("code_patches")
                    .select("*")
                    .in_("finding_id", finding_ids)
                    .execute()
                )
                patches = [CodePatchSchema(**p) for p in (patches_res.data or [])]
            except Exception:
                pass

        if not patches and audit_id in _IN_MEMORY_PATCHES:
            import uuid
            for p in _IN_MEMORY_PATCHES[audit_id]:
                p_dict = p.copy() if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else dict(p))
                p_dict.setdefault("patch_id", str(uuid.uuid4()))
                p_dict.setdefault("created_at", str(audit_data.get("created_at", "")))
                patches.append(CodePatchSchema(**p_dict))


        audit_response = AuditResponse(
            audit_id=str(audit_data["audit_id"]),
            organization_id=str(audit_data["organization_id"]),
            project_name=audit_data["project_name"],
            target_url=audit_data["target_url"],
            repository_url=audit_data.get("repository_url"),
            status=audit_data["status"],
            compliance_score=audit_data.get("compliance_score"),
            state_hash=audit_data.get("state_hash"),
            created_at=str(audit_data["created_at"]),
            updated_at=str(audit_data["updated_at"]),
        )

        return ApiResponse(
            data=AuditContextStateResponse(
                audit=audit_response,
                governance_promises=[],
                findings=findings,
                generated_patches=patches,
            ),
            error=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit {audit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit: {e!s}",
        ) from e


@router.get("/audits/{audit_id}/stream")
@router.get("/api/v1/audits/{audit_id}/stream")
@router.get("/audits/{audit_id}/telemetry")
@router.get("/api/v1/audits/{audit_id}/telemetry")
async def stream_audit_telemetry(
    audit_id: str,
    session: UserSession = Depends(get_current_user_session),
    supabase: Client = Depends(get_supabase_client),
) -> StreamingResponse:
    """Streams real-time audit telemetry events using Server-Sent Events (SSE)."""
    # Verify audit exists and belongs to this organization
    current_status = "IN_PROGRESS"
    found = False
    try:
        audit_res = (
            supabase.table("audits")
            .select("audit_id, status, organization_id")
            .eq("audit_id", audit_id)
            .eq("organization_id", session.organization_id)
            .limit(1)
            .execute()
        )
        if audit_res.data and len(audit_res.data) > 0:
            current_status = audit_res.data[0]["status"]
            found = True
    except Exception:
        pass

    if not found:
        if audit_id in _IN_MEMORY_AUDITS and _IN_MEMORY_AUDITS[audit_id]["organization_id"] == session.organization_id:
            current_status = _IN_MEMORY_AUDITS[audit_id]["status"]
            found = True

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit '{audit_id}' not found or does not belong to your organization",
        )


    async def event_generator() -> AsyncGenerator[str, None]:
        # Emit initial status frame
        init_frame = {
            "audit_id": audit_id,
            "status": current_status,
            "event_type": "STATUS_UPDATE",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        yield f"event: status\ndata: {json.dumps(init_frame)}\n\n"

        # Emit telemetry connect frame
        telemetry_frame = {
            "audit_id": audit_id,
            "agent_role": "synthesis_agent",
            "panel": "terminal",
            "level": "info",
            "message": f"Audit {audit_id} telemetry stream active",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        yield f"event: telemetry\ndata: {json.dumps(telemetry_frame)}\n\n"

        # Keep-alive heartbeat
        await asyncio.sleep(0.05)
        ping_frame = {"ping": True, "timestamp": datetime.now(UTC).isoformat()}
        yield f"event: ping\ndata: {json.dumps(ping_frame)}\n\n"

        if current_status in ["COMPLETED", "FAILED"]:
            return

        event_bus = get_event_bus()
        subscriber = event_bus.subscribe("*")
        try:
            while True:
                try:
                    # Non-blocking poll on subscriber generator with 15s timeout
                    msg = await asyncio.wait_for(subscriber.__anext__(), timeout=15.0)
                    topic = msg.get("event")
                    payload = msg.get("payload", {})

                    if payload.get("audit_id") == audit_id:
                        if topic == "TELEMETRY_LOG":
                            yield f"event: telemetry\ndata: {json.dumps(payload)}\n\n"
                        elif topic == "AUDIT_COMPLETED":
                            yield f"event: status\ndata: {json.dumps(payload)}\n\n"
                            break
                except TimeoutError:
                    # Emit periodic keepalive heartbeat ping
                    ping_frame = {"ping": True, "timestamp": datetime.now(UTC).isoformat()}
                    yield f"event: ping\ndata: {json.dumps(ping_frame)}\n\n"
                except StopAsyncIteration:
                    break
        finally:
            if hasattr(subscriber, "aclose"):
                await subscriber.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
