from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SeverityEnum(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AuditStatusEnum(StrEnum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentRoleEnum(StrEnum):
    SYNTHESIS_AGENT = "synthesis_agent"
    POLICY_AGENT = "policy_agent"
    FRONTEND_AGENT = "frontend_agent"
    BACKEND_AGENT = "backend_agent"
    INCIDENT_MANAGEMENT_AGENT = "incident_management_agent"
    CHILD_SAFETY_AGENT = "child_safety_agent"
    DPR_PORTAL_AGENT = "dpr_portal_agent"


class ComplianceFrameworkEnum(StrEnum):
    DPDP_ACT_2023 = "DPDP_ACT_2023"
    DPDP_RULES_2025 = "DPDP_RULES_2025"
    BOTH = "BOTH"


# ------------------------------------------------------------------------------
# Request Schemas
# ------------------------------------------------------------------------------
class CreateAuditRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Organization audit project name",
    )
    target_url: str = Field(..., description="Target web application URL")
    repository_url: str | None = Field(None, description="Optional GitHub/GitLab repository URL")
    framework: ComplianceFrameworkEnum = Field(
        default=ComplianceFrameworkEnum.BOTH,
        description="Statutory compliance framework",
    )
    legal_doc_reference: str | None = Field(
        None, description="Uploaded legal document reference / filename"
    )


# ------------------------------------------------------------------------------
# Response Schemas
# ------------------------------------------------------------------------------
class FindingSchema(BaseModel):
    finding_id: str
    audit_id: str
    agent_role: str
    act_section: str
    rules_clause: str
    severity: SeverityEnum
    title: str
    description: str
    evidence_snippet: str
    remediation_suggestion: str
    created_at: str


class CodePatchSchema(BaseModel):
    patch_id: str
    finding_id: str
    file_path: str
    original_code: str
    patched_code: str
    diff_content: str
    status: str
    created_at: str


class AuditResponse(BaseModel):
    audit_id: str
    organization_id: str
    project_name: str
    target_url: str
    repository_url: str | None = None
    status: AuditStatusEnum
    compliance_score: int | None = None
    state_hash: str | None = None
    created_at: str
    updated_at: str


class AuditContextStateResponse(BaseModel):
    audit: AuditResponse
    governance_promises: list[dict[str, Any]] = []
    findings: list[FindingSchema] = []
    generated_patches: list[CodePatchSchema] = []


class ApiResponse[T](BaseModel):
    data: T | None = None
    error: str | None = None
