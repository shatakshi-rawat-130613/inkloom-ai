"""Acceptance and integration tests for organisation-aware routing, brand isolation,
role-specific destinations, and secure organisation lookup."""

import pytest
from fastapi.testclient import TestClient

from app.enums import UserRole
from app.main import app


@pytest.fixture
def client(seeded_db):
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ------------------------------------------------------------------------------
# 1. ORGANISATION LOOKUP
# ------------------------------------------------------------------------------

def test_organisation_lookup_privacy_and_security(client):
    # Register an organisation
    res = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Helios Health Corp",
            "display_name": "Dr. Henry",
            "email": "henry@helios.internal",
            "password": "Password123!",
        },
    )
    assert res.status_code == 201

    # Exact slug match
    lookup_slug = client.get("/api/auth/organisations/lookup?code=helios-health-corp")
    assert lookup_slug.status_code == 200
    d_slug = lookup_slug.json()
    assert d_slug["exists"] is True
    assert d_slug["name"] == "Helios Health Corp"
    assert d_slug["slug"] == "helios-health-corp"
    # Ensure no private tenant members, emails, or counts are returned
    assert "users" not in d_slug
    assert "email" not in d_slug
    assert "password" not in d_slug

    # Partial name match
    lookup_name = client.get("/api/auth/organisations/lookup?query=Helios")
    assert lookup_name.status_code == 200
    d_name = lookup_name.json()
    assert d_name["exists"] is True
    assert d_name["name"] == "Helios Health Corp"

    # Non-existent organisation lookup
    lookup_none = client.get("/api/auth/organisations/lookup?query=NonExistentCorp99")
    assert lookup_none.status_code == 200
    d_none = lookup_none.json()
    assert d_none["exists"] is False
    assert d_none["name"] is None

    # Too short query (min length guard)
    lookup_short = client.get("/api/auth/organisations/lookup?query=h")
    assert lookup_short.status_code == 200
    assert lookup_short.json()["exists"] is False


# ------------------------------------------------------------------------------
# 2. BRAND ROUTING & ISOLATION
# ------------------------------------------------------------------------------

def test_single_brand_organisation_routing(client):
    # Register Org 1
    res = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Vanguard Skincare",
            "display_name": "Valerie",
            "email": "valerie@vanguard.internal",
            "password": "Password123!",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    org_id = res.json()["user"]["organisation_id"]

    # Before creating any brand: 0 organisation brands
    brands_res0 = client.get("/api/brands", headers={"Authorization": f"Bearer {token}"})
    assert brands_res0.status_code == 200
    org_brands0 = [b for b in brands_res0.json() if b.get("organisation_id") == org_id]
    assert len(org_brands0) == 0

    # Create exactly one brand
    b_res = client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Vanguard Pure",
            "industry": "Skincare",
            "description": "Minimalist restorative skincare.",
            "voice_summary": "Clean, scientific, and transparent.",
        },
    )
    assert b_res.status_code == 201
    brand1_id = b_res.json()["id"]

    # After creating 1 brand: exactly 1 organisation brand
    brands_res1 = client.get("/api/brands", headers={"Authorization": f"Bearer {token}"})
    assert brands_res1.status_code == 200
    org_brands1 = [b for b in brands_res1.json() if b.get("organisation_id") == org_id]
    assert len(org_brands1) == 1
    assert org_brands1[0]["id"] == brand1_id
    assert org_brands1[0]["name"] == "Vanguard Pure"


def test_multi_brand_organisation_routing(client):
    # Register Org 2
    res = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Apex Consumer Goods",
            "display_name": "Arthur",
            "email": "arthur@apex.internal",
            "password": "Password123!",
        },
    )
    token = res.json()["access_token"]
    org_id = res.json()["user"]["organisation_id"]

    # Create Brand A
    client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Apex Botanicals",
            "industry": "Beauty",
            "description": "Herbal formulas.",
            "voice_summary": "Natural and grounded.",
        },
    )

    # Create Brand B
    client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Apex Nutrition",
            "industry": "Wellness",
            "description": "Targeted supplements.",
            "voice_summary": "Energetic and factual.",
        },
    )

    # List brands returns both brands for this organisation
    brands_res = client.get("/api/brands", headers={"Authorization": f"Bearer {token}"})
    org_brands = [b for b in brands_res.json() if b.get("organisation_id") == org_id]
    assert len(org_brands) == 2
    names = {b["name"] for b in org_brands}
    assert "Apex Botanicals" in names
    assert "Apex Nutrition" in names


def test_cross_tenant_brand_access_rejected(client):
    # Tenant 1
    res1 = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Tenant One Corp",
            "display_name": "User One",
            "email": "one@tenant1.internal",
            "password": "Password123!",
        },
    )
    token1 = res1.json()["access_token"]
    brand_res = client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "name": "Tenant One Brand",
            "industry": "Cosmetics",
            "description": "Private brand for tenant one.",
            "voice_summary": "Exclusive voice.",
        },
    )
    brand1_id = brand_res.json()["id"]

    # Tenant 2
    res2 = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Tenant Two Corp",
            "display_name": "User Two",
            "email": "two@tenant2.internal",
            "password": "Password123!",
        },
    )
    token2 = res2.json()["access_token"]

    # Tenant 2 attempts to fetch Tenant 1's brand by ID
    get_res = client.get(f"/api/brands/{brand1_id}", headers={"Authorization": f"Bearer {token2}"})
    assert get_res.status_code == 404

    # Tenant 2 attempts to submit content to Tenant 1's brand
    sub_res = client.post(
        "/api/submissions",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "brand_id": brand1_id,
            "title": "Malicious Cross-Tenant Submission",
            "content_type": "social_post",
            "body": "Cross tenant payload.",
            "author_name": "Intruder",
        },
    )
    assert sub_res.status_code == 404

    # Stale non-existent brand ID returns 404
    stale_res = client.get(
        "/api/brands/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert stale_res.status_code == 404


# ------------------------------------------------------------------------------
# 3. DEMO ROLES & LOGIN PARITY
# ------------------------------------------------------------------------------

def test_demo_role_logins_resolve_lumacare_brand(client):
    demo_roles = [
        ("admin@lumacare.demo", UserRole.ADMIN),
        ("editor@lumacare.demo", UserRole.EDITOR),
        ("reviewer@lumacare.demo", UserRole.REVIEWER),
    ]

    for email, expected_role in demo_roles:
        login_res = client.post(
            "/api/auth/login",
            json={"email": email, "password": "LumaCareDemo2026!"},
        )
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert data["user"]["role"] == expected_role.value
        token = data["access_token"]

        # Fetch authorised brands
        brands_res = client.get("/api/brands", headers={"Authorization": f"Bearer {token}"})
        assert brands_res.status_code == 200
        brands = brands_res.json()
        demo_brands = [b for b in brands if b["is_demo"] is True]
        assert len(demo_brands) >= 1
        assert any(b["name"] == "LumaCare" for b in demo_brands)
