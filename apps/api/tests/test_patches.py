from datetime import UTC, datetime
from unittest.mock import MagicMock
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


def test_get_finding_patch_success() -> None:
    """GET /findings/{id}/patch returns the code patch for a finding scoped to the organization."""
    org_id = str(uuid4())
    audit_id = str(uuid4())
    finding_id = str(uuid4())
    patch_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)

    mock_supabase = MagicMock()

    mock_finding_check = [{"finding_id": finding_id, "audit_id": audit_id}]
    sample_diff = (
        "--- a/user_controller.py\n"
        "+++ b/user_controller.py\n"
        "@@ -14,1 +14,1 @@\n"
        '-logger.info("User KYC: aadhaar=%s", user.aadhaar)\n'
        '+logger.info("User KYC: aadhaar_hash=%s", hash_pii(user.aadhaar))'
    )
    mock_patch = {
        "patch_id": patch_id,
        "finding_id": finding_id,
        "file_path": "apps/api/controllers/user_controller.py",
        "original_code": 'logger.info("User KYC: aadhaar=%s", user.aadhaar)',
        "patched_code": 'logger.info("User KYC: aadhaar_hash=%s", hash_pii(user.aadhaar))',
        "diff_content": sample_diff,
        "status": "PENDING_REVIEW",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    def mock_table(table_name: str):
        mock_builder = MagicMock()
        if table_name == "audit_findings":
            m_select = mock_builder.select.return_value
            m_chain = MagicMock()
            m_chain.eq.return_value = m_chain
            m_chain.limit.return_value.execute.return_value = MagicMock(data=mock_finding_check)
            m_select.eq.return_value = m_chain
        elif table_name == "code_patches":
            m_select = mock_builder.select.return_value
            m_select.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[mock_patch]
            )
        return mock_builder

    mock_supabase.table.side_effect = mock_table
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.get(f"/findings/{finding_id}/patch", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["patch_id"] == patch_id
        assert data["finding_id"] == finding_id
        assert data["status"] == "PENDING_REVIEW"
        assert "diff_content" in data
    finally:
        app.dependency_overrides.clear()


def test_get_finding_patch_cross_org_isolation() -> None:
    """GET /findings/{id}/patch rejects access to another organization's finding with 404."""
    org_a = str(uuid4())
    finding_b = str(uuid4())
    headers_a = make_auth_header(org_id=org_a)

    mock_supabase = MagicMock()
    # Finding check returns empty for Org A
    m_sel = mock_supabase.table.return_value.select.return_value
    m_sel.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.get(f"/findings/{finding_b}/patch", headers=headers_a)
        assert response.status_code == 404
        assert "not found or access denied" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_approve_patch_success() -> None:
    """POST /patches/{id}/approve updates status to APPLIED."""
    org_id = str(uuid4())
    patch_id = str(uuid4())
    finding_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)

    mock_supabase = MagicMock()

    mock_patch_check = [{"patch_id": patch_id, "finding_id": finding_id}]
    mock_updated_patch = {
        "patch_id": patch_id,
        "finding_id": finding_id,
        "file_path": "apps/api/controllers/user_controller.py",
        "original_code": "orig",
        "patched_code": "patched",
        "diff_content": "diff",
        "status": "APPLIED",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    def mock_table(table_name: str):
        mock_builder = MagicMock()
        if table_name == "code_patches":
            m_select = mock_builder.select.return_value
            m_chain = MagicMock()
            m_chain.eq.return_value = m_chain
            m_chain.limit.return_value.execute.return_value = MagicMock(data=mock_patch_check)
            m_select.eq.return_value = m_chain

            m_update = mock_builder.update.return_value
            m_update.eq.return_value.execute.return_value = MagicMock(data=[mock_updated_patch])
        return mock_builder

    mock_supabase.table.side_effect = mock_table
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.post(f"/patches/{patch_id}/approve", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["patch_id"] == patch_id
        assert data["status"] == "APPLIED"
    finally:
        app.dependency_overrides.clear()


def test_reject_patch_success() -> None:
    """POST /patches/{id}/reject updates status to REJECTED."""
    org_id = str(uuid4())
    patch_id = str(uuid4())
    finding_id = str(uuid4())
    headers = make_auth_header(org_id=org_id)

    mock_supabase = MagicMock()

    mock_patch_check = [{"patch_id": patch_id, "finding_id": finding_id}]
    mock_updated_patch = {
        "patch_id": patch_id,
        "finding_id": finding_id,
        "file_path": "apps/api/controllers/user_controller.py",
        "original_code": "orig",
        "patched_code": "patched",
        "diff_content": "diff",
        "status": "REJECTED",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }

    def mock_table(table_name: str):
        mock_builder = MagicMock()
        if table_name == "code_patches":
            m_select = mock_builder.select.return_value
            m_chain = MagicMock()
            m_chain.eq.return_value = m_chain
            m_chain.limit.return_value.execute.return_value = MagicMock(data=mock_patch_check)
            m_select.eq.return_value = m_chain

            m_update = mock_builder.update.return_value
            m_update.eq.return_value.execute.return_value = MagicMock(data=[mock_updated_patch])
        return mock_builder

    mock_supabase.table.side_effect = mock_table
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.post(f"/patches/{patch_id}/reject", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["patch_id"] == patch_id
        assert data["status"] == "REJECTED"
    finally:
        app.dependency_overrides.clear()


def test_patch_operations_cross_org_rejected() -> None:
    """POST /patches/{id}/approve rejects cross-organization access with 404."""
    org_a = str(uuid4())
    patch_b = str(uuid4())
    headers_a = make_auth_header(org_id=org_a)

    mock_supabase = MagicMock()
    m_sel = mock_supabase.table.return_value.select.return_value
    m_sel.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        response = client.post(f"/patches/{patch_b}/approve", headers=headers_a)
        assert response.status_code == 404
        assert "not found or access denied" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
