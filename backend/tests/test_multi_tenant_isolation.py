"""Tests proving strict multi-tenant data isolation and preventing cross-tenant data leaks."""

import pytest
from fastapi.testclient import TestClient

from app.enums import ContentType, ReviewDecision
from app.main import app


@pytest.fixture
def client(seeded_db):
    """TestClient sharing the seeded test database."""
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_strict_multi_tenant_data_isolation(client):
    # =========================================================================
    # Step 1: Register Tenant 1 (Solar Care)
    # =========================================================================
    t1_reg = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Solar Care Labs",
            "display_name": "Sarah Solar",
            "email": "sarah@solar.com",
            "password": "Password123!",
        },
    ).json()
    t1_token = t1_reg["access_token"]
    t1_headers = {"Authorization": f"Bearer {t1_token}"}

    # Tenant 1 creates Brand 1
    b1_res = client.post(
        "/api/brands",
        headers=t1_headers,
        json={
            "name": "Solar Shield SPF",
            "industry": "Skincare",
            "description": "Daily mineral sun protection.",
            "voice_summary": "Protective, scientific, clear.",
        },
    )
    assert b1_res.status_code == 201
    b1_id = b1_res.json()["id"]

    # Tenant 1 creates Submission 1
    s1_res = client.post(
        "/api/submissions",
        headers=t1_headers,
        json={
            "brand_id": b1_id,
            "title": "Solar Morning Routine",
            "content_type": ContentType.SOCIAL_POST,
            "body": "Apply solar protection every morning before outdoor activity.",
        },
    )
    assert s1_res.status_code == 201
    s1_id = s1_res.json()["id"]

    # Tenant 1 analyzes Submission 1
    run1_res = client.post(f"/api/submissions/{s1_id}/analyze", headers=t1_headers)
    assert run1_res.status_code == 201
    run1_id = run1_res.json()["id"]

    # =========================================================================
    # Step 2: Register Tenant 2 (Lunar Beauty)
    # =========================================================================
    t2_reg = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Lunar Beauty Corp",
            "display_name": "Leo Lunar",
            "email": "leo@lunar.com",
            "password": "Password123!",
        },
    ).json()
    t2_token = t2_reg["access_token"]
    t2_headers = {"Authorization": f"Bearer {t2_token}"}

    # Tenant 2 creates Brand 2
    b2_res = client.post(
        "/api/brands",
        headers=t2_headers,
        json={
            "name": "Lunar Night Renewal",
            "industry": "Cosmetics",
            "description": "Overnight hydrating essence.",
            "voice_summary": "Soothing and restorative.",
        },
    )
    assert b2_res.status_code == 201
    b2_id = b2_res.json()["id"]

    # Tenant 2 creates Submission 2
    s2_res = client.post(
        "/api/submissions",
        headers=t2_headers,
        json={
            "brand_id": b2_id,
            "title": "Night Renewal Ritual",
            "content_type": ContentType.SOCIAL_POST,
            "body": "Nourish your skin overnight with lunar botanical oils.",
        },
    )
    assert s2_res.status_code == 201
    s2_id = s2_res.json()["id"]

    # Tenant 2 analyzes Submission 2
    run2_res = client.post(f"/api/submissions/{s2_id}/analyze", headers=t2_headers)
    assert run2_res.status_code == 201
    run2_id = run2_res.json()["id"]

    # =========================================================================
    # Step 3: Verify Tenant 1 CANNOT view or tamper with Tenant 2's data
    # =========================================================================

    # Tenant 1 cannot fetch Brand 2
    assert client.get(f"/api/brands/{b2_id}", headers=t1_headers).status_code == 404

    # Tenant 1 cannot update Brand 2
    assert client.patch(
        f"/api/brands/{b2_id}",
        headers=t1_headers,
        json={"name": "Hacked Brand Name"},
    ).status_code == 404

    # Tenant 1 cannot add guidelines to Brand 2
    assert client.post(
        f"/api/brands/{b2_id}/guidelines",
        headers=t1_headers,
        json={
            "code": "HACK-001",
            "title": "Malicious Rule",
            "rule_text": "Bad guideline rule",
            "category": "outcome_claim",
            "default_severity": "high",
        },
    ).status_code == 404

    # Tenant 1 cannot add visual assets to Brand 2
    assert client.post(
        f"/api/brands/{b2_id}/assets",
        headers=t1_headers,
        json={
            "asset_type": "logo",
            "name": "Fake Logo",
            "asset_metadata": {"hacked": True},
        },
    ).status_code == 404

    # Tenant 1 cannot fetch Submission 2
    assert client.get(f"/api/submissions/{s2_id}", headers=t1_headers).status_code == 404

    # Tenant 1 cannot add versions to Submission 2
    assert client.post(
        f"/api/submissions/{s2_id}/versions",
        headers=t1_headers,
        json={"body": "Injected malicious version text"},
    ).status_code == 404

    # Tenant 1 cannot trigger re-analysis of Submission 2
    assert client.post(f"/api/submissions/{s2_id}/analyze", headers=t1_headers).status_code == 404

    # Tenant 1 cannot record reviews on Submission 2
    assert client.post(
        f"/api/submissions/{s2_id}/reviews",
        headers=t1_headers,
        json={
            "decision": ReviewDecision.APPROVED,
            "reviewer_name": "Sarah Solar",
            "comments": "Malicious cross-tenant review approval.",
        },
    ).status_code == 404

    # Tenant 1 cannot view audit trail of Submission 2
    assert client.get(f"/api/submissions/{s2_id}/audit", headers=t1_headers).status_code == 404

    # Tenant 1 cannot access Analysis Run 2 directly
    assert client.get(f"/api/analysis-runs/{run2_id}", headers=t1_headers).status_code == 404

    # =========================================================================
    # Step 4: Verify List endpoints strictly isolate listings
    # =========================================================================

    # Brands list for Tenant 1 includes Brand 1 and public demo LumaCare, but NOT Brand 2
    t1_brands = client.get("/api/brands", headers=t1_headers).json()
    t1_brand_ids = {b["id"] for b in t1_brands}
    assert b1_id in t1_brand_ids
    assert b2_id not in t1_brand_ids

    # Submissions list for Tenant 1 includes Submission 1, but NOT Submission 2
    t1_subs = client.get("/api/submissions", headers=t1_headers).json()
    t1_sub_ids = {s["id"] for s in t1_subs}
    assert s1_id in t1_sub_ids
    assert s2_id not in t1_sub_ids

    # Brands list for Tenant 2 includes Brand 2, but NOT Brand 1
    t2_brands = client.get("/api/brands", headers=t2_headers).json()
    t2_brand_ids = {b["id"] for b in t2_brands}
    assert b2_id in t2_brand_ids
    assert b1_id not in t2_brand_ids

    # Submissions list for Tenant 2 includes Submission 2, but NOT Submission 1
    t2_subs = client.get("/api/submissions", headers=t2_headers).json()
    t2_sub_ids = {s["id"] for s in t2_subs}
    assert s2_id in t2_sub_ids
    assert s1_id not in t2_sub_ids
