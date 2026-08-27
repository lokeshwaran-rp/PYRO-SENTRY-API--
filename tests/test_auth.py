"""
Authentication & RBAC test suite for PYRO-SENTRY API.
Covers register, login, refresh, profile, logout, invalid credentials, token revocation, and RBAC rejection.
"""

import pytest
from fastapi.testclient import TestClient


def test_register_user_success(unauth_client: TestClient):
    """Test successful user registration."""
    payload = {
        "email": "newuser@pyrosentry.io",
        "username": "newuser",
        "password": "Password123!",
        "role": "ANALYST",
    }
    response = unauth_client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@pyrosentry.io"
    assert data["username"] == "newuser"
    assert data["role"] == "ANALYST"
    assert "id" in data
    assert "created_at" in data


def test_register_duplicate_email(unauth_client: TestClient):
    """Test rejection when registering with existing email."""
    payload = {
        "email": "operator@pyrosentry.io",  # Existing seed email
        "username": "unique_username",
        "password": "Password123!",
    }
    response = unauth_client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_register_duplicate_username(unauth_client: TestClient):
    """Test rejection when registering with existing username."""
    payload = {
        "email": "another@pyrosentry.io",
        "username": "operator_user",  # Existing seed username
        "password": "Password123!",
    }
    response = unauth_client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert "already taken" in response.json()["detail"].lower()


def test_login_success(unauth_client: TestClient):
    """Test successful login with email and password."""
    payload = {
        "email": "operator@pyrosentry.io",
        "password": "OperatorPass123!",
    }
    response = unauth_client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(unauth_client: TestClient):
    """Test login rejection with incorrect password."""
    payload = {
        "email": "operator@pyrosentry.io",
        "password": "WrongPassword999!",
    }
    response = unauth_client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user(unauth_client: TestClient):
    """Test login rejection for unknown email."""
    payload = {
        "email": "ghost@pyrosentry.io",
        "password": "Password123!",
    }
    response = unauth_client.post("/auth/login", json=payload)
    assert response.status_code == 401


def test_get_current_user_profile(client: TestClient):
    """Test GET /auth/me for authenticated user."""
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "operator@pyrosentry.io"
    assert data["role"] == "OPERATOR"
    assert data["is_active"] is True


def test_get_current_user_unauthorized(unauth_client: TestClient):
    """Test GET /auth/me without token fails with 401."""
    response = unauth_client.get("/auth/me")
    assert response.status_code == 401


def test_token_refresh_flow(unauth_client: TestClient):
    """Test refreshing tokens using a valid refresh token."""
    # 1. Login to obtain refresh token
    login_res = unauth_client.post(
        "/auth/login",
        json={"email": "analyst@pyrosentry.io", "password": "AnalystPass123!"},
    )
    tokens = login_res.json()
    refresh_tok = tokens["refresh_token"]

    # 2. Refresh token
    refresh_res = unauth_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_tok},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # 3. New access token works
    test_client = TestClient(unauth_client.app)
    test_client.headers.update({"Authorization": f"Bearer {new_tokens['access_token']}"})
    me_res = test_client.get("/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "analyst@pyrosentry.io"


def test_logout_and_revocation(unauth_client: TestClient):
    """Test logging out revokes refresh token and blocks further refreshes."""
    # 1. Login
    login_res = unauth_client.post(
        "/auth/login",
        json={"email": "admin@pyrosentry.io", "password": "AdminPass123!"},
    )
    refresh_tok = login_res.json()["refresh_token"]
    access_tok = login_res.json()["access_token"]

    # 2. Logout
    auth_client = TestClient(unauth_client.app)
    auth_client.headers.update({"Authorization": f"Bearer {access_tok}"})
    logout_res = auth_client.post("/auth/logout", json={"refresh_token": refresh_tok})
    assert logout_res.status_code == 200
    assert "logged out" in logout_res.json()["message"].lower()

    # 3. Attempting to use the revoked refresh token must fail with 401
    fail_res = unauth_client.post("/auth/refresh", json={"refresh_token": refresh_tok})
    assert fail_res.status_code == 401


def test_rbac_viewer_blocked_from_operator_actions(viewer_client: TestClient):
    """Test that VIEWER role is rejected with 403 when attempting mutating operator actions."""
    # Acknowledge threat requires OPERATOR+
    response = viewer_client.post(
        "/api/v1/threats/threat-501/acknowledge",
        json={"operator_name": "Viewer"},
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"] or "role" in response.json()["detail"].lower()

    # Create event requires OPERATOR+
    event_payload = {
        "title": "Unauthorized Event",
        "latitude": 30.0,
        "longitude": -95.0,
        "severity": "LOW",
        "source": "MANUAL",
        "description": "Viewer cannot create",
    }
    event_res = viewer_client.post("/api/v1/events", json=event_payload)
    assert event_res.status_code == 403
