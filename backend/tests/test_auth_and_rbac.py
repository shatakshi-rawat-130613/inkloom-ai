"""Tests for authentication flows, JWT validation and Role-Based Access Control."""

import pytest
from fastapi.testclient import TestClient

from app.enums import ContentType, ReviewDecision, SubmissionStatus, UserRole
from app.main import app


@pytest.fixture
def client(seeded_db):
    """TestClient sharing the seeded test database."""
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_register_creates_org_and_admin(client):
    res = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Acme Health Labs",
            "display_name": "Alice Admin",
            "email": "alice@acme.com",
            "password": "Password123!",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    user = data["user"]
    assert user["display_name"] == "Alice Admin"
    assert user["email"] == "alice@acme.com"
    assert user["role"] == "admin"
    assert user["organisation_name"] == "Acme Health Labs"


def test_register_duplicate_email_fails(client):
    payload = {
        "organisation_name": "Beta Corp",
        "display_name": "Bob Beta",
        "email": "bob@beta.com",
        "password": "Password123!",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


def test_login_success_and_me(client):
    client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Calm Care",
            "display_name": "Charlie Manager",
            "email": "charlie@calm.com",
            "password": "SecurePassword456!",
        },
    )

    login_res = client.post(
        "/api/auth/login",
        json={"email": "charlie@calm.com", "password": "SecurePassword456!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["email"] == "charlie@calm.com"
    assert me["role"] == "admin"


def test_login_invalid_password(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "editor@lumacare.demo", "password": "WrongPassword!"},
    )
    assert res.status_code == 401


def test_admin_can_add_members_with_roles(client):
    # Register Admin
    reg = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Omni Brand",
            "display_name": "Omni Boss",
            "email": "boss@omni.com",
            "password": "Password123!",
        },
    ).json()
    admin_token = reg["access_token"]

    # Admin creates an Editor
    res_ed = client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "display_name": "Omni Creator",
            "email": "creator@omni.com",
            "password": "Password123!",
            "role": "editor",
        },
    )
    assert res_ed.status_code == 201
    assert res_ed.json()["role"] == "editor"

    # Admin creates a Reviewer
    res_rev = client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "display_name": "Omni Auditor",
            "email": "auditor@omni.com",
            "password": "Password123!",
            "role": "reviewer",
        },
    )
    assert res_rev.status_code == 201
    assert res_rev.json()["role"] == "reviewer"

    # Verify listing members
    members_res = client.get("/api/auth/members", headers={"Authorization": f"Bearer {admin_token}"})
    assert members_res.status_code == 200
    emails = {m["email"] for m in members_res.json()}
    assert emails == {"boss@omni.com", "creator@omni.com", "auditor@omni.com"}


def test_non_admin_cannot_create_members(client):
    # Register Admin & create Editor
    reg = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Delta Co",
            "display_name": "Delta Admin",
            "email": "admin@delta.com",
            "password": "Password123!",
        },
    ).json()

    ed_res = client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
        json={
            "display_name": "Delta Editor",
            "email": "editor@delta.com",
            "password": "Password123!",
            "role": "editor",
        },
    ).json()

    # Log in as Editor
    login_ed = client.post(
        "/api/auth/login",
        json={"email": "editor@delta.com", "password": "Password123!"},
    ).json()
    editor_token = login_ed["access_token"]

    # Editor attempts to invite another user -> 403 Forbidden
    hack_res = client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={
            "display_name": "Sneaky User",
            "email": "sneaky@delta.com",
            "password": "Password123!",
            "role": "admin",
        },
    )
    assert hack_res.status_code == 403


def test_rbac_content_creator_cannot_review_and_reviewer_cannot_submit(client):
    # Setup Org with Brand, Editor, and Reviewer
    admin = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Glow Naturals",
            "display_name": "Glow Admin",
            "email": "admin@glow.com",
            "password": "Password123!",
        },
    ).json()
    admin_token = admin["access_token"]

    # Create Brand
    brand = client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Glow Facial Serum",
            "industry": "Skincare",
            "description": "Pure botanical skincare products.",
            "voice_summary": "Authentic and scientific.",
        },
    ).json()
    brand_id = brand["id"]

    # Add Editor
    client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "display_name": "Glow Writer",
            "email": "writer@glow.com",
            "password": "Password123!",
            "role": "editor",
        },
    )

    # Add Reviewer
    client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "display_name": "Glow Compliance",
            "email": "compliance@glow.com",
            "password": "Password123!",
            "role": "reviewer",
        },
    )

    editor_token = client.post(
        "/api/auth/login", json={"email": "writer@glow.com", "password": "Password123!"}
    ).json()["access_token"]

    reviewer_token = client.post(
        "/api/auth/login", json={"email": "compliance@glow.com", "password": "Password123!"}
    ).json()["access_token"]

    # Negative test 1: Reviewer cannot create submissions
    rev_sub_res = client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "brand_id": brand_id,
            "title": "Unauthorized Reviewer Submission",
            "content_type": ContentType.SOCIAL_POST,
            "body": "This post should not be allowed.",
        },
    )
    assert rev_sub_res.status_code == 403

    # Positive test: Editor creates submission
    ed_sub_res = client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={
            "brand_id": brand_id,
            "title": "Summer Botanical Campaign",
            "content_type": ContentType.SOCIAL_POST,
            "body": "Introducing our gentle facial serum for daily nourishment.",
        },
    )
    assert ed_sub_res.status_code == 201
    sub_id = ed_sub_res.json()["id"]

    # Analyze and submit for review
    client.post(f"/api/submissions/{sub_id}/analyze", headers={"Authorization": f"Bearer {editor_token}"})
    client.post(f"/api/submissions/{sub_id}/review-request", headers={"Authorization": f"Bearer {editor_token}"})

    # Negative test 2: Editor cannot approve/review their own submission
    ed_review_res = client.post(
        f"/api/submissions/{sub_id}/reviews",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={
            "decision": ReviewDecision.APPROVED,
            "reviewer_name": "Glow Writer",
            "comments": "Self-approving my own content.",
        },
    )
    assert ed_review_res.status_code == 403

    # Positive test: Reviewer records review
    rev_review_res = client.post(
        f"/api/submissions/{sub_id}/reviews",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "decision": ReviewDecision.APPROVED,
            "reviewer_name": "Glow Compliance",
            "comments": "Approved after factual check.",
        },
    )
    assert rev_review_res.status_code == 201
    assert rev_review_res.json()["status"] == "approved"
