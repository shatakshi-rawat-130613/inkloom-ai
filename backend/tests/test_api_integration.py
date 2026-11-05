"""Comprehensive API integration tests covering the complete 11-step workflow."""

from fastapi.testclient import TestClient

from app.db import get_db
from app.enums import OverallStatus, ReviewDecision, SubmissionStatus
from app.main import app
from tests.fixtures.lumacare_cases import COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT


def test_health_endpoints(db):
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    app.dependency_overrides.clear()


def test_brands_endpoint(seeded_db):
    app.dependency_overrides[get_db] = lambda: seeded_db
    client = TestClient(app)

    res = client.get("/api/brands")
    assert res.status_code == 200
    brands = res.json()
    assert len(brands) >= 1
    assert any(b["slug"] == "lumacare" for b in brands)

    res_detail = client.get("/api/brands/lumacare")
    assert res_detail.status_code == 200
    brand = res_detail.json()
    assert brand["name"] == "LumaCare"
    assert len(brand["guidelines"]) == 3
    assert len(brand["facts"]) == 2
    assert len(brand["terms"]) == 1
    app.dependency_overrides.clear()


def test_complete_e2e_workflow(seeded_db):
    app.dependency_overrides[get_db] = lambda: seeded_db
    client = TestClient(app)

    # 1. Fetch brand
    brand = client.get("/api/brands/lumacare").json()
    brand_id = brand["id"]

    # 2. Submit initial non-compliant draft (Test Case 1)
    sub_payload = {
        "brand_id": brand_id,
        "title": "Spring Campaign Ad",
        "content_type": "advertisement",
        "body": NON_COMPLIANT.content,
        "author_name": "Demo Editor",
    }
    create_res = client.post("/api/submissions", json=sub_payload)
    assert create_res.status_code == 201
    sub_detail = create_res.json()
    sub_id = sub_detail["id"]
    assert sub_detail["status"] == SubmissionStatus.DRAFT
    assert sub_detail["current_version_number"] == 1
    assert "analyze" in sub_detail["allowed_actions"]

    # 3. Run Analysis on v1
    analysis_res = client.post(f"/api/submissions/{sub_id}/analyze")
    assert analysis_res.status_code == 201
    run1 = analysis_res.json()
    assert run1["overall_status"] == OverallStatus.NON_COMPLIANT
    assert run1["finding_count"] > 0
    assert run1["requires_human_review"] is True

    # Check updated submission
    sub_after_run1 = client.get(f"/api/submissions/{sub_id}").json()
    assert sub_after_run1["status"] == SubmissionStatus.ANALYZED
    assert sub_after_run1["latest_overall_status"] == OverallStatus.NON_COMPLIANT
    assert "request_review" in sub_after_run1["allowed_actions"]

    # 4. Create Revision v2 (Test Case 2: Compliant)
    v2_payload = {
        "body": COMPLIANT.content,
        "change_note": "Replaced guarantees with approved gentle approach",
    }
    v2_res = client.post(f"/api/submissions/{sub_id}/versions", json=v2_payload)
    assert v2_res.status_code == 201
    sub_v2 = v2_res.json()
    assert sub_v2["current_version_number"] == 2
    assert sub_v2["status"] == SubmissionStatus.DRAFT

    # 5. Run Analysis on v2
    analysis_v2_res = client.post(f"/api/submissions/{sub_id}/analyze")
    assert analysis_v2_res.status_code == 201
    run2 = analysis_v2_res.json()
    # No blockers on v2
    assert not any(f["severity"] in ("critical", "high") for f in run2["findings"])

    # 6. Submit for Human Review
    req_res = client.post(f"/api/submissions/{sub_id}/review-request", json={"requested_by": "Demo Editor", "note": "Ready for approval"})
    assert req_res.status_code == 200
    sub_in_review = req_res.json()
    assert sub_in_review["status"] == SubmissionStatus.IN_REVIEW
    assert "review" in sub_in_review["allowed_actions"]

    # 7. Human Reviewer Approves
    review_payload = {
        "decision": ReviewDecision.APPROVED,
        "reviewer_name": "Senior Brand Lead",
        "comments": "Approved. Excellent compliance and tone.",
    }
    rev_res = client.post(f"/api/submissions/{sub_id}/reviews", json=review_payload)
    assert rev_res.status_code == 201
    sub_approved = rev_res.json()
    assert sub_approved["status"] == SubmissionStatus.APPROVED
    assert len(sub_approved["reviews"]) == 1
    assert sub_approved["reviews"][0]["decision"] == ReviewDecision.APPROVED

    # 8. Check Audit Trail
    audit_res = client.get(f"/api/submissions/{sub_id}/audit")
    assert audit_res.status_code == 200
    audit_entries = audit_res.json()
    actions = [e["action"] for e in audit_entries]
    assert "submission_created" in actions
    assert "analysis_completed" in actions
    assert "version_created" in actions
    assert "review_requested" in actions
    assert "review_recorded" in actions

    # 9. Verify History Preservation
    final_sub = client.get(f"/api/submissions/{sub_id}").json()
    assert len(final_sub["versions"]) == 2
    assert len(final_sub["analysis_runs"]) == 2
    assert final_sub["versions"][0]["body"] == NON_COMPLIANT.content
    assert final_sub["versions"][1]["body"] == COMPLIANT.content

    app.dependency_overrides.clear()


def test_partially_compliant_flow_with_revision_request(seeded_db):
    app.dependency_overrides[get_db] = lambda: seeded_db
    client = TestClient(app)

    brand = client.get("/api/brands/lumacare").json()

    # Submit Test Case 3 (Partially compliant)
    create_res = client.post(
        "/api/submissions",
        json={
            "brand_id": brand["id"],
            "title": "Social Campaign Post",
            "content_type": "social_post",
            "body": PARTIALLY_COMPLIANT.content,
        },
    )
    sub_id = create_res.json()["id"]

    # Analyze
    run_res = client.post(f"/api/submissions/{sub_id}/analyze")
    assert run_res.status_code == 201
    assert run_res.json()["overall_status"] == OverallStatus.NEEDS_REVIEW

    # Request review
    client.post(f"/api/submissions/{sub_id}/review-request")

    # Reviewer requests revisions
    rev_res = client.post(
        f"/api/submissions/{sub_id}/reviews",
        json={
            "decision": ReviewDecision.REVISIONS_REQUESTED,
            "reviewer_name": "Compliance Lead",
            "comments": "Please remove the unapproved 7-day timeframe before publishing.",
        },
    )
    assert rev_res.status_code == 201
    assert rev_res.json()["status"] == SubmissionStatus.REVISIONS_REQUESTED

    # Ensure author can create another version
    v2_res = client.post(
        f"/api/submissions/{sub_id}/versions",
        json={"body": COMPLIANT.content, "change_note": "Removed 7-day timeframe"},
    )
    assert v2_res.status_code == 201
    assert v2_res.json()["status"] == SubmissionStatus.DRAFT

    app.dependency_overrides.clear()
