from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt
from apps.api.auth import get_supabase_client
from apps.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
TEST_SECRET = "super-secret-jwt-key-for-testing-purposes-32chars"


def make_auth_header(org_id: str | None = None, user_id: str | None = None) -> dict[str, str]:
    u_id = user_id or str(uuid4())
    o_id = org_id or str(uuid4())
    token = jwt.encode(
        {
            "sub": u_id,
            "email": "test@org.com",
            "app_metadata": {"organization_id": o_id, "role": "ADMIN"},
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_audit_immediate_response() -> None:
    """POST /audits returns an audit_id immediately without agent execution."""
    org_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)
    audit_id = str(uuid4())

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[
            {
                "audit_id": audit_id,
                "organization_id": org_id,
                "project_name": "Acme Portal",
                "target_url": "https://example.com",
                "status": "IN_PROGRESS",
            }
        ]
    )

    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        payload = {
            "project_name": "Acme Portal",
            "target_url": "https://example.com",
            "repository_url": "https://github.com/acme/portal",
            "framework": "BOTH",
        }
        with patch("apps.api.routers.audits.run_audit_pipeline"):
            start_time = datetime.now(UTC)
            response = client.post("/audits", json=payload, headers=headers)
            duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        assert response.status_code == 201
        assert duration_ms < 500  # Well under a second
        data = response.json()
        assert data["data"]["audit_id"] == audit_id
        assert data["data"]["status"] == "IN_PROGRESS"
        assert data["data"]["organization_id"] == org_id
        assert data["error"] is None
    finally:
        app.dependency_overrides.clear()


def test_create_audit_rejects_malformed_input() -> None:
    """Pydantic layer rejects invalid/missing fields with structured 422 error."""
    headers = make_auth_header()

    # Missing target_url
    response = client.post("/audits", json={"project_name": "Test"}, headers=headers)
    assert response.status_code == 422
    assert "target_url" in str(response.json())

    # Empty project name
    bad_payload = {"project_name": "", "target_url": "https://example.com"}
    response = client.post("/audits", json=bad_payload, headers=headers)
    assert response.status_code == 422


def test_cross_org_isolation_on_get_audit() -> None:
    """User from Org A cannot access an audit belonging to Org B."""
    org_a = str(uuid4())
    audit_b = str(uuid4())

    headers_a = make_auth_header(org_id=org_a)

    mock_supabase = MagicMock()
    # Simulating that Org B owns the audit, so Org A query returns empty
    mock_eq = mock_supabase.table.return_value.select.return_value.eq.return_value.eq
    mock_eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.get(f"/audits/{audit_b}", headers=headers_a)
        assert response.status_code == 404
        assert "not found or does not belong to your organization" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_audit_snapshot_with_findings() -> None:
    """GET /audits/{id} returns full state snapshot for the owning organization."""
    org_id = str(uuid4())
    audit_id = str(uuid4())
    finding_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)

    mock_supabase = MagicMock()

    mock_audit = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Security Audit",
        "target_url": "https://example.com",
        "status": "COMPLETED",
        "compliance_score": 85,
        "state_hash": "hash123",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    mock_finding = {
        "finding_id": finding_id,
        "audit_id": audit_id,
        "agent_role": "frontend_agent",
        "act_section": "Section 6(1)",
        "rules_clause": "Rule 3(2)",
        "severity": "CRITICAL",
        "title": "Pre-consent tracker detected",
        "description": "Network request fired before consent banner action",
        "evidence_snippet": "GET https://tracker.com/pixel",
        "remediation_suggestion": "Defer tracker execution until consent granted",
        "created_at": datetime.now(UTC).isoformat(),
    }

    def mock_table(table_name: str):
        mock_builder = MagicMock()
        if table_name == "audits":
            m_select = mock_builder.select.return_value
            m_select.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
                MagicMock(data=[mock_audit])
            )
        elif table_name == "audit_findings":
            m_findings = mock_builder.select.return_value
            m_findings.eq.return_value.order.return_value.execute.return_value = (
                MagicMock(data=[mock_finding])
            )
        elif table_name == "code_patches":
            mock_builder.select.return_value.in_.return_value.execute.return_value = (
                MagicMock(data=[])
            )
        return mock_builder

    mock_supabase.table.side_effect = mock_table
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.get(f"/audits/{audit_id}", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["audit"]["audit_id"] == audit_id
        assert body["data"]["audit"]["compliance_score"] == 85
        assert len(body["data"]["findings"]) == 1
        assert body["data"]["findings"][0]["severity"] == "CRITICAL"
        assert body["data"]["findings"][0]["act_section"] == "Section 6(1)"
    finally:
        app.dependency_overrides.clear()


def test_get_audit_zero_findings_compliant() -> None:
    """GET /audits/{id} for zero-findings audit returns score 100 and empty findings."""
    org_id = str(uuid4())
    audit_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)

    mock_supabase = MagicMock()

    mock_audit = {
        "audit_id": audit_id,
        "organization_id": org_id,
        "project_name": "Fully Compliant Audit",
        "target_url": "https://clean-app.example.com",
        "status": "COMPLETED",
        "compliance_score": 100,
        "state_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    def mock_table(table_name: str):
        mock_builder = MagicMock()
        if table_name == "audits":
            m_select = mock_builder.select.return_value
            m_select.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
                MagicMock(data=[mock_audit])
            )
        elif table_name == "audit_findings":
            m_findings = mock_builder.select.return_value
            m_findings.eq.return_value.order.return_value.execute.return_value = (
                MagicMock(data=[])
            )
        elif table_name == "code_patches":
            mock_builder.select.return_value.in_.return_value.execute.return_value = (
                MagicMock(data=[])
            )
        return mock_builder

    mock_supabase.table.side_effect = mock_table
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.get(f"/audits/{audit_id}", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["audit"]["audit_id"] == audit_id
        assert body["data"]["audit"]["compliance_score"] == 100
        assert body["data"]["findings"] == []
        assert body["data"]["generated_patches"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_audit_unauthorized_without_token() -> None:
    """GET /audits/{id} without authorization header rejects with 401."""
    response = client.get("/audits/any-id")
    assert response.status_code == 401


def test_stream_audit_telemetry_sse() -> None:
    """GET /audits/{id}/stream opens SSE and emits status and telemetry event frames."""
    org_id = str(uuid4())
    audit_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)

    mock_supabase = MagicMock()
    m_eq = mock_supabase.table.return_value.select.return_value.eq.return_value.eq
    m_eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"audit_id": audit_id, "status": "IN_PROGRESS", "organization_id": org_id}]
    )

    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.get(f"/audits/{audit_id}/stream", headers=headers)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        content = response.text
        assert "event: status" in content
        assert "event: telemetry" in content
        assert "event: ping" in content
        assert audit_id in content
    finally:
        app.dependency_overrides.clear()
