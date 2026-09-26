from unittest.mock import MagicMock
from uuid import uuid4

import jwt
from apps.api.auth import get_supabase_client
from apps.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
TEST_SECRET = "super-secret-jwt-key-for-testing-purposes-32chars"


def test_unauthenticated_request_rejected() -> None:
    """Check that requests without authorization header receive 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Authentication credentials required" in response.json()["detail"]


def test_invalid_token_rejected() -> None:
    """Check that requests with invalid JWT tokens receive 401."""
    headers = {"Authorization": "Bearer not-a-valid-token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


def test_token_without_sub_rejected() -> None:
    """Check that tokens missing the 'sub' user ID claim are rejected."""
    token = jwt.encode({"email": "test@example.com"}, TEST_SECRET, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "missing sub claim" in response.json()["detail"]


def test_authenticated_user_with_app_metadata_org() -> None:
    """Check that a user with organization_id receives their scope."""
    user_id = str(uuid4())
    org_id = str(uuid4())
    token = jwt.encode(
        {
            "sub": user_id,
            "email": "auditor@acme.com",
            "app_metadata": {
                "organization_id": org_id,
                "role": "ADMIN",
            },
        },
        TEST_SECRET,
        algorithm="HS256",
    )

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["organization_id"] == org_id
    assert data["role"] == "ADMIN"
    assert data["email"] == "auditor@acme.com"


def test_two_different_org_users_isolation() -> None:
    """Check that User A and User B from different orgs resolve distinct scopes."""
    user_a = str(uuid4())
    org_a = str(uuid4())
    token_a = jwt.encode(
        {
            "sub": user_a,
            "email": "user_a@company-a.com",
            "app_metadata": {"organization_id": org_a, "role": "ADMIN"},
        },
        TEST_SECRET,
        algorithm="HS256",
    )

    user_b = str(uuid4())
    org_b = str(uuid4())
    token_b = jwt.encode(
        {
            "sub": user_b,
            "email": "user_b@company-b.com",
            "app_metadata": {"organization_id": org_b, "role": "MEMBER"},
        },
        TEST_SECRET,
        algorithm="HS256",
    )

    # Request A
    res_a = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    assert res_a.json()["organization_id"] == org_a
    assert res_a.json()["user_id"] == user_a

    # Request B
    res_b = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["organization_id"] == org_b
    assert res_b.json()["user_id"] == user_b

    # Ensure scopes are strictly non-overlapping
    assert res_a.json()["organization_id"] != res_b.json()["organization_id"]


def test_user_org_resolved_from_database() -> None:
    """Check that missing JWT org_id is resolved from organization_members table."""
    user_id = str(uuid4())
    org_id = str(uuid4())
    token = jwt.encode({"sub": user_id, "email": "test@db.com"}, TEST_SECRET, algorithm="HS256")

    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"organization_id": org_id, "role": "ADMIN"}]
    mock_table = mock_supabase.table.return_value
    mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["organization_id"] == org_id
        assert data["role"] == "ADMIN"
    finally:
        app.dependency_overrides.clear()
