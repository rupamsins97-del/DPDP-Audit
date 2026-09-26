import operator
from typing import Annotated, Any

from typing_extensions import TypedDict


def merge_dicts(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Merges two dictionaries."""
    res = dict(a)
    res.update(b)
    return res


class AuditContextState(TypedDict, total=False):
    """The central state schema for the LangGraph 360° compliance audit pipeline."""

    audit_id: str
    organization_id: str
    project_name: str
    target_url: str
    repository_url: str | None
    framework: str
    status: str
    uploaded_documents: list[Any] | None

    # Reducer: Append findings from parallel workers
    governance_promises: Annotated[list[dict[str, Any]], operator.add]
    findings: Annotated[list[dict[str, Any]], operator.add]
    generated_patches: Annotated[list[dict[str, Any]], operator.add]

    compliance_score: int | None
    state_hash: str | None
    error: str | None
