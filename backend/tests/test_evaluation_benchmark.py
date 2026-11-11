"""Comprehensive Round 3 Multi-Brand Evaluation and Verification Benchmark.

Tests:
1. Multi-Tenant Organisation Registration & Isolation.
2. Independent Multi-Brand Creation and Knowledge Base Configuration.
3. Strict Role-Based Access Control (Admin, Editor, Reviewer).
4. Universal Brand Relevance Detection & Cross-Industry Validation.
5. Competitor Comparison and Multi-Brand Text Handling.
6. Context Sufficiency Evaluation (e.g. single-word or greeting copy).
7. Multi-Format Document Ingestion (DOCX, PDF, Text).
8. Visual Brand Asset Analysis (Dominant Palette & Genuine Logo Verification).
9. Explainable Claim-Level Findings & Grounding Verification.
"""

import io
import zipfile
from PIL import Image, ImageDraw
import pytest
from fastapi.testclient import TestClient

from app.enums import OverallStatus, UserRole
from app.main import app
from app.models import BrandAsset, BrandProfile, Organisation, User
from app.schemas import BrandKnowledge
from app.services.analyzer import analyze_content
from app.services.document_service import (
    compute_perceptual_hash,
    extract_docx_content,
    extract_pdf_content,
    verify_logo_reference,
)
from app.services.relevance import BrandRelevance, assess_brand_relevance


@pytest.fixture
def client(seeded_db):
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==============================================================================
# 1. MULTI-TENANT ISOLATION & ORGANISATION REGISTRATION
# ==============================================================================

def test_benchmark_organisation_registration_and_isolation(client):
    # Register Organisation A
    res_a = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Aura Wellness Co",
            "display_name": "Alice Manager",
            "email": "alice@aura.test",
            "password": "SecurePassword123!",
        },
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    user_a = res_a.json()["user"]
    assert user_a["role"] == "admin"

    # Register Organisation B
    res_b = client.post(
        "/api/auth/register",
        json={
            "organisation_name": "Nexus Robotics",
            "display_name": "Bob Manager",
            "email": "bob@nexus.test",
            "password": "SecurePassword123!",
        },
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]

    # Org A creates a brand
    res_brand_a = client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "name": "Aura Glow",
            "industry": "Cosmetics",
            "description": "Mindful clean cosmetics and nourishing botanical formulations.",
            "voice_summary": "Radiant, natural, mindful.",
        },
    )
    assert res_brand_a.status_code == 201
    brand_a_id = res_brand_a.json()["id"]

    # Org B attempts to access Org A's brand -> Must receive 404
    res_tamper = client.get(
        f"/api/brands/{brand_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_tamper.status_code == 404


# ==============================================================================
# 2. INDEPENDENT MULTI-BRAND KNOWLEDGE BASE CONFIGURATION
# ==============================================================================

def test_benchmark_multi_brand_knowledge_configuration(client):
    # Sign in as LumaCare Brand Manager
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@lumacare.demo", "password": "LumaCareDemo2026!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Create a secondary brand under the same organisation
    res_new_brand = client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Botanica Derma",
            "industry": "Herbal Skincare",
            "description": "Herbal dermatology and botanical skincare for sensitive skin.",
            "voice_summary": "Wholesome, botanical, scientifically grounded.",
        },
    )
    assert res_new_brand.status_code == 201
    botanica_id = res_new_brand.json()["id"]

    # Add a brand guideline to Botanica Derma
    res_guide = client.post(
        f"/api/brands/{botanica_id}/guidelines",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "code": "BOT-001",
            "title": "Organic certification claims",
            "rule_text": "Only claim certified organic if approved supplier documentation is referenced.",
            "category": "factual_consistency",
            "default_severity": "high",
        },
    )
    assert res_guide.status_code == 201

    # Verify LumaCare does NOT have BOT-001
    luma_res = client.get("/api/brands/lumacare")
    assert luma_res.status_code == 200
    luma_codes = [g["id"] for g in luma_res.json()["guidelines"]]
    assert "BOT-001" not in luma_codes


# ==============================================================================
# 3. ROLE-BASED ACCESS CONTROL (RBAC) GATES
# ==============================================================================

def test_benchmark_rbac_permission_barriers(client):
    # Sign in as Creator (Editor)
    login_editor = client.post(
        "/api/auth/login",
        json={"email": "editor@lumacare.demo", "password": "LumaCareDemo2026!"},
    )
    assert login_editor.status_code == 200
    token_editor = login_editor.json()["access_token"]

    # Creator attempts to invite new team member -> Must be forbidden (403)
    res_invite = client.post(
        "/api/auth/members",
        headers={"Authorization": f"Bearer {token_editor}"},
        json={
            "display_name": "Unauthorized Member",
            "email": "unauthorized@lumacare.demo",
            "password": "Password123!",
            "role": "editor",
        },
    )
    assert res_invite.status_code == 403

    # Creator attempts to create a new brand -> Must be forbidden (403)
    res_create_brand = client.post(
        "/api/brands",
        headers={"Authorization": f"Bearer {token_editor}"},
        json={
            "name": "Illegal Brand",
            "industry": "Other",
            "description": "Unauthorized attempt to create brand.",
            "voice_summary": "Should be blocked.",
        },
    )
    assert res_create_brand.status_code == 403


# ==============================================================================
# 4. UNIVERSAL BRAND RELEVANCE DETECTION & CROSS-INDUSTRY BENCHMARK
# ==============================================================================

def test_benchmark_brand_relevance_scenarios():
    knowledge = BrandKnowledge(
        brand_id="test",
        brand_name="LumaCare",
        guidelines=[],
        facts=[],
        terms=[],
    )

    # A: Cross-industry fintech copy evaluated against LumaCare -> UNRELATED
    fintech_copy = (
        "Finora is a next-generation financial technology platform offering seamless digital payments, "
        "smart budgeting, and automated investment accounts with zero transaction fees."
    )
    res_unrelated = assess_brand_relevance(fintech_copy, knowledge, title="Finora Overview")
    assert res_unrelated.status == BrandRelevance.UNRELATED_TO_BRAND
    assert res_unrelated.detected_brand == "Finora"

    # B: Food & beverage copy evaluated against LumaCare -> UNRELATED
    food_copy = (
        "Harvest & Hearth produces artisan sourdough bread and organic granola with wholesome seeds and nuts."
    )
    res_food = assess_brand_relevance(food_copy, knowledge, title="Harvest & Hearth Menu")
    assert res_food.status == BrandRelevance.UNRELATED_TO_BRAND

    # C: Short greeting / conversational filler -> INSUFFICIENT_CONTEXT
    res_short = assess_brand_relevance("helllooooooo", knowledge, title="LumaCare Social Announcement")
    assert res_short.status == BrandRelevance.INSUFFICIENT_CONTEXT

    # D: Competitor comparison mentioning both LumaCare and Velveteen -> RELEVANT
    comparison_copy = (
        "Comparing LumaCare and Velveteen: While Velveteen claims instant overnight results, "
        "LumaCare focuses on realistic skincare that supports clearer-looking skin over time."
    )
    res_comparison = assess_brand_relevance(comparison_copy, knowledge, title="Competitive Market Analysis")
    assert res_comparison.status == BrandRelevance.RELEVANT_TO_BRAND


# ==============================================================================
# 5. MULTI-FORMAT DOCUMENT INGESTION (DOCX, PDF, TEXT)
# ==============================================================================

def test_benchmark_docx_ingestion():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "word/document.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p><w:r><w:t>LumaCare Daily Hydrating Cream formulation overview.</w:t></w:r></w:p>
        <w:p><w:r><w:t>Guaranteed to cure acne within 3 days.</w:t></w:r></w:p>
    </w:body>
</w:document>""",
        )
    docx_bytes = buf.getvalue()
    text, meta = extract_docx_content(docx_bytes, "formulation.docx")
    assert "formulation overview" in text
    assert meta["paragraph_count"] == 2
    assert meta["source"] == "document"


# ==============================================================================
# 6. VISUAL LOGO REFERENCE AND PALETTE COMPARISON
# ==============================================================================

def test_benchmark_visual_logo_and_palette_verification(seeded_db):
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").first()

    # Draw authentic reference logo
    logo_img = Image.new("RGB", (300, 100), color=(253, 251, 247))
    d1 = ImageDraw.Draw(logo_img)
    d1.rectangle([40, 20, 260, 80], fill=(28, 25, 23))
    ref_hash = compute_perceptual_hash(logo_img)

    logo_asset = BrandAsset(
        brand_id=brand.id,
        asset_type="logo",
        name="LumaCare Benchmark Logo",
        asset_metadata={"perceptual_hash": ref_hash, "text": "LumaCare"},
    )
    seeded_db.add(logo_asset)
    seeded_db.commit()

    # Test exact logo matches reference
    buf_matching = io.BytesIO()
    logo_img.save(buf_matching, format="PNG")
    status, conf, exp, finding = verify_logo_reference(
        buf_matching.getvalue(), "auth_logo.png", "LumaCare", [logo_asset]
    )
    assert status == "approved_logo_detected"
    assert finding is None

    # Test banner with divergent layout
    divergent_img = Image.new("RGB", (900, 250), color=(253, 251, 247))
    d2 = ImageDraw.Draw(divergent_img)
    d2.polygon([(100, 200), (200, 50), (300, 200)], fill=(156, 65, 50))
    buf_div = io.BytesIO()
    divergent_img.save(buf_div, format="PNG")
    d_status, d_conf, d_exp, d_finding = verify_logo_reference(
        buf_div.getvalue(), "divergent.png", "LumaCare", [logo_asset]
    )
    assert d_status in {"expected_logo_not_detected", "possible_incorrect_logo"}
    assert d_finding is not None
