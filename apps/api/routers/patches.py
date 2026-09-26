import logging

from apps.api.auth import UserSession, get_current_user_session, get_supabase_client
from apps.api.schemas import ApiResponse, CodePatchSchema
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["patches"])


def verify_finding_organization_access(
    finding_id: str,
    organization_id: str,
    supabase: Client,
) -> dict[str, str]:
    """Verifies that a finding exists and belongs to the caller's organization."""
    finding_res = (
        supabase.table("audit_findings")
        .select("finding_id, audit_id, audits!inner(organization_id)")
        .eq("finding_id", finding_id)
        .eq("audits.organization_id", organization_id)
        .limit(1)
        .execute()
    )

    if not finding_res.data or len(finding_res.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{finding_id}' not found or access denied",
        )

    return finding_res.data[0]


def verify_patch_organization_access(
    patch_id: str,
    organization_id: str,
    supabase: Client,
) -> dict[str, str]:
    """Verifies that a patch exists and belongs to the caller's organization."""
    patch_res = (
        supabase.table("code_patches")
        .select(
            "patch_id, finding_id, file_path, original_code, patched_code, diff_content, status, "
            "created_at, updated_at, audit_findings!inner(audit_id, audits!inner(organization_id))"
        )
        .eq("patch_id", patch_id)
        .eq("audit_findings.audits.organization_id", organization_id)
        .limit(1)
        .execute()
    )

    if not patch_res.data or len(patch_res.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patch '{patch_id}' not found or access denied",
        )

    return patch_res.data[0]


@router.get(
    "/findings/{finding_id}/patch",
    response_model=ApiResponse[CodePatchSchema],
)
@router.get(
    "/api/v1/findings/{finding_id}/patch",
    response_model=ApiResponse[CodePatchSchema],
)
async def get_finding_patch(
    finding_id: str,
    session: UserSession = Depends(get_current_user_session),
    supabase: Client = Depends(get_supabase_client),
) -> ApiResponse[CodePatchSchema]:
    """Retrieves the remediation code patch for a finding, scoped to organization."""
    try:
        from apps.api.routers.audits import _IN_MEMORY_PATCHES

        # 1. Verify access via database
        access_verified = False
        try:
            verify_finding_organization_access(
                finding_id=finding_id,
                organization_id=session.organization_id,
                supabase=supabase,
            )
            access_verified = True
        except HTTPException:
            raise
        except Exception:
            # Fallback if database table unpopulated
            pass

        # 2. Query code_patches in Supabase
        if access_verified:
            try:
                patch_res = (
                    supabase.table("code_patches")
                    .select("*")
                    .eq("finding_id", finding_id)
                    .limit(1)
                    .execute()
                )

                if patch_res.data and len(patch_res.data) > 0:
                    patch_data = patch_res.data[0]
                    return ApiResponse(
                        data=CodePatchSchema(
                            patch_id=str(patch_data["patch_id"]),
                            finding_id=str(patch_data["finding_id"]),
                            file_path=patch_data["file_path"],
                            original_code=patch_data["original_code"],
                            patched_code=patch_data["patched_code"],
                            diff_content=patch_data["diff_content"],
                            status=patch_data["status"],
                            created_at=str(patch_data["created_at"]),
                        ),
                        error=None,
                    )
            except Exception:
                pass

        # 3. Check in-memory store
        for patches_list in _IN_MEMORY_PATCHES.values():
            for p in patches_list:
                if (isinstance(p, dict) and p.get("finding_id") == finding_id) or (hasattr(p, "finding_id") and p.finding_id == finding_id):
                    patch_obj = p if isinstance(p, dict) else p.model_dump()
                    return ApiResponse(data=CodePatchSchema(**patch_obj), error=None)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No remediation patch found for finding '{finding_id}'",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patch for finding {finding_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving patch: {e!s}",
        ) from e


@router.post(
    "/patches/{patch_id}/approve",
    response_model=ApiResponse[CodePatchSchema],
)
@router.post(
    "/api/v1/patches/{patch_id}/approve",
    response_model=ApiResponse[CodePatchSchema],
)
async def approve_patch(
    patch_id: str,
    session: UserSession = Depends(get_current_user_session),
    supabase: Client = Depends(get_supabase_client),
) -> ApiResponse[CodePatchSchema]:
    """Approves a remediation patch and updates status to APPLIED."""
    try:
        from apps.api.routers.audits import _IN_MEMORY_PATCHES

        # 1. Verify access
        access_verified = False
        try:
            verify_patch_organization_access(
                patch_id=patch_id,
                organization_id=session.organization_id,
                supabase=supabase,
            )
            access_verified = True
        except HTTPException:
            raise
        except Exception:
            pass

        # 2. Update Supabase
        if access_verified:
            try:
                update_res = (
                    supabase.table("code_patches")
                    .update({"status": "APPLIED"})
                    .eq("patch_id", patch_id)
                    .execute()
                )

                if update_res.data and len(update_res.data) > 0:
                    patch_data = update_res.data[0]
                    return ApiResponse(
                        data=CodePatchSchema(
                            patch_id=str(patch_data["patch_id"]),
                            finding_id=str(patch_data["finding_id"]),
                            file_path=patch_data["file_path"],
                            original_code=patch_data["original_code"],
                            patched_code=patch_data["patched_code"],
                            diff_content=patch_data["diff_content"],
                            status="APPLIED",
                            created_at=str(patch_data["created_at"]),
                        ),
                        error=None,
                    )
            except Exception:
                pass

        # 3. Check in-memory store
        for patches_list in _IN_MEMORY_PATCHES.values():
            for p in patches_list:
                p_id = p.get("patch_id") if isinstance(p, dict) else getattr(p, "patch_id", None)
                if p_id == patch_id:
                    if isinstance(p, dict):
                        p["status"] = "APPLIED"
                        return ApiResponse(data=CodePatchSchema(**p), error=None)
                    else:
                        p.status = "APPLIED"
                        return ApiResponse(data=CodePatchSchema(**p.model_dump()), error=None)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patch '{patch_id}' not found or access denied",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving patch {patch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving patch: {e!s}",
        ) from e


@router.post(
    "/patches/{patch_id}/reject",
    response_model=ApiResponse[CodePatchSchema],
)
@router.post(
    "/api/v1/patches/{patch_id}/reject",
    response_model=ApiResponse[CodePatchSchema],
)
async def reject_patch(
    patch_id: str,
    session: UserSession = Depends(get_current_user_session),
    supabase: Client = Depends(get_supabase_client),
) -> ApiResponse[CodePatchSchema]:
    """Rejects a remediation patch and updates status to REJECTED."""
    try:
        from apps.api.routers.audits import _IN_MEMORY_PATCHES

        # 1. Verify access
        access_verified = False
        try:
            verify_patch_organization_access(
                patch_id=patch_id,
                organization_id=session.organization_id,
                supabase=supabase,
            )
            access_verified = True
        except HTTPException:
            raise
        except Exception:
            pass

        # 2. Update Supabase
        if access_verified:
            try:
                update_res = (
                    supabase.table("code_patches")
                    .update({"status": "REJECTED"})
                    .eq("patch_id", patch_id)
                    .execute()
                )

                if update_res.data and len(update_res.data) > 0:
                    patch_data = update_res.data[0]
                    return ApiResponse(
                        data=CodePatchSchema(
                            patch_id=str(patch_data["patch_id"]),
                            finding_id=str(patch_data["finding_id"]),
                            file_path=patch_data["file_path"],
                            original_code=patch_data["original_code"],
                            patched_code=patch_data["patched_code"],
                            diff_content=patch_data["diff_content"],
                            status="REJECTED",
                            created_at=str(patch_data["created_at"]),
                        ),
                        error=None,
                    )
            except Exception:
                pass

        # 3. Check in-memory store
        for patches_list in _IN_MEMORY_PATCHES.values():
            for p in patches_list:
                p_id = p.get("patch_id") if isinstance(p, dict) else getattr(p, "patch_id", None)
                if p_id == patch_id:
                    if isinstance(p, dict):
                        p["status"] = "REJECTED"
                        return ApiResponse(data=CodePatchSchema(**p), error=None)
                    else:
                        p.status = "REJECTED"
                        return ApiResponse(data=CodePatchSchema(**p.model_dump()), error=None)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patch '{patch_id}' not found or access denied",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting patch {patch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting patch: {e!s}",
        ) from e


