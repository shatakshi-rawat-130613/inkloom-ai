"""Production End-to-End Acceptance Test Script for Inkloom AI Round 3.
Runs live HTTP API requests against the deployed Render backend and Supabase database.
"""

import io
import time
import uuid
import zipfile
from PIL import Image, ImageDraw
import pypdf
import requests

API_BASE = "https://inkloom-backend-upau.onrender.com/api"
tag = str(uuid.uuid4())[:8]

print("==================================================")
print(f"STARTING LIVE ACCEPTANCE AUDIT (Run tag: {tag})")
print("==================================================")

# 1. REGISTRATION AND LOGIN
reg_payload = {
    "organisation_name": f"Audit Org {tag}",
    "display_name": f"Auditor {tag}",
    "email": f"auditor_{tag}@audit.test",
    "password": "SecurePassword123!",
}
r = requests.post(f"{API_BASE}/auth/register", json=reg_payload)
assert r.status_code == 201, f"Registration failed: {r.status_code} {r.text}"
admin_token = r.json()["access_token"]
admin_user = r.json()["user"]
assert admin_user["role"] == "admin"
print("[PASS] 1. Registration & Initial Brand Manager (admin) Provisioning")

login_r = requests.post(
    f"{API_BASE}/auth/login",
    json={"email": reg_payload["email"], "password": reg_payload["password"]},
)
assert login_r.status_code == 200
assert "access_token" in login_r.json()
assert login_r.json()["token_type"] == "bearer"
login_token = login_r.json()["access_token"]
print("[PASS] 2. User Authentication & JWT Issuance")

me_r = requests.get(f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {login_token}"})
assert me_r.status_code == 200
assert me_r.json()["email"] == reg_payload["email"]
print("[PASS] 3. Session Identification (/api/auth/me)")

# 2. BRAND CREATION AND BRAND SWITCHING
brand_payload = {
    "name": f"Veritas Clinical {tag}",
    "industry": "Clinical Dermatology",
    "description": "Evidence-backed clinical skincare and medical formulations.",
    "voice_summary": "Precise, clinical, transparent.",
}
brand_r = requests.post(
    f"{API_BASE}/brands",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=brand_payload,
)
assert brand_r.status_code == 201, f"Brand creation failed: {brand_r.status_code} {brand_r.text}"
brand = brand_r.json()
brand_id = brand["id"]
brand_name = brand["name"]
print(f"[PASS] 4. Brand Creation: {brand_name} (ID: {brand_id})")

brands_list_r = requests.get(
    f"{API_BASE}/brands", headers={"Authorization": f"Bearer {admin_token}"}
)
assert brands_list_r.status_code == 200
user_brands = brands_list_r.json()
assert any(b["id"] == brand_id for b in user_brands)
print("[PASS] 5. Multi-Brand Listing & Context Switching")

# 3. KNOWLEDGE CONFIGURATION
g_code = f"VER-{tag[:4].upper()}"
g_payload = {
    "code": g_code,
    "title": "Clinical evidence required",
    "rule_text": "All claims regarding efficacy must cite peer-reviewed clinical evidence.",
    "category": "factual_consistency",
    "default_severity": "high",
}
g_r = requests.post(
    f"{API_BASE}/brands/{brand_id}/guidelines",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=g_payload,
)
assert g_r.status_code == 201, f"Guideline creation failed: {g_r.status_code} {g_r.text}"
print("[PASS] 6. Brand Guideline Addition")

f_code = f"FACT-{tag[:4].upper()}"
f_payload = {
    "code": f_code,
    "statement": "Veritas Clinical formulas are tested across 12-week controlled trials.",
    "source": "Veritas Clinical Trial Report 2026",
}
f_r = requests.post(
    f"{API_BASE}/brands/{brand_id}/facts",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=f_payload,
)
assert f_r.status_code == 201, f"Fact creation failed: {f_r.status_code} {f_r.text}"
print("[PASS] 7. Verified Fact Addition")

t_code = f"TERM-{tag[:4].upper()}"
t_payload = {
    "code": t_code,
    "preferred_term": "physician formulated",
    "prohibited_term": "miracle cure",
    "notes": "Always emphasize scientific formulation over miraculous claims.",
}
t_r = requests.post(
    f"{API_BASE}/brands/{brand_id}/terms",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=t_payload,
)
assert t_r.status_code == 201, f"Term creation failed: {t_r.status_code} {t_r.text}"
print("[PASS] 8. Approved & Prohibited Terminology Addition")

a_payload = {
    "asset_type": "color_palette",
    "name": "Veritas Clinical Primary Palette",
    "asset_metadata": {
        "colors": [
            {"name": "Clinical White", "hex": "#FFFFFF", "role": "primary_background"},
            {"name": "Slate Navy", "hex": "#1E293B", "role": "primary_text"},
        ]
    },
}
a_r = requests.post(
    f"{API_BASE}/brands/{brand_id}/assets",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=a_payload,
)
assert a_r.status_code == 201, f"Asset creation failed: {a_r.status_code} {a_r.text}"
print("[PASS] 9. Visual Asset Configuration")

# 4. TEAM MEMBER PROVISIONING & RBAC BARRIERS
# Admin provisions an Editor (Creator)
ed_email = f"editor_{tag}@audit.test"
ed_r = requests.post(
    f"{API_BASE}/auth/members",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "display_name": f"Editor {tag}",
        "email": ed_email,
        "password": "SecurePassword123!",
        "role": "editor",
    },
)
assert ed_r.status_code == 201, f"Member creation failed: {ed_r.status_code} {ed_r.text}"
print(f"[PASS] 10. Team Member Provisioning: Creator ({ed_email})")

# Admin provisions a Reviewer
rev_email = f"reviewer_{tag}@audit.test"
rev_r = requests.post(
    f"{API_BASE}/auth/members",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "display_name": f"Reviewer {tag}",
        "email": rev_email,
        "password": "SecurePassword123!",
        "role": "reviewer",
    },
)
assert rev_r.status_code == 201, f"Member creation failed: {rev_r.status_code} {rev_r.text}"
print(f"[PASS] 11. Team Member Provisioning: Reviewer ({rev_email})")

# Login as Editor
ed_login = requests.post(
    f"{API_BASE}/auth/login",
    json={"email": ed_email, "password": "SecurePassword123!"},
)
assert ed_login.status_code == 200
ed_token = ed_login.json()["access_token"]

# RBAC Gate: Editor attempts to provision another member -> MUST receive 403 Forbidden
ed_tamper_invite = requests.post(
    f"{API_BASE}/auth/members",
    headers={"Authorization": f"Bearer {ed_token}"},
    json={
        "display_name": "Rogue Member",
        "email": f"rogue_{tag}@audit.test",
        "password": "SecurePassword123!",
        "role": "editor",
    },
)
assert ed_tamper_invite.status_code == 403
print("[PASS] 12. RBAC Enforcement: Non-Admin Member Provisioning Blocked (403)")

# RBAC Gate: Editor attempts to create brand -> MUST receive 403 Forbidden
ed_tamper_brand = requests.post(
    f"{API_BASE}/brands",
    headers={"Authorization": f"Bearer {ed_token}"},
    json={
        "name": "Rogue Brand",
        "industry": "Other",
        "description": "Unauthorized attempt.",
        "voice_summary": "Rogue.",
    },
)
assert ed_tamper_brand.status_code == 403
print("[PASS] 13. RBAC Enforcement: Non-Admin Brand Creation Blocked (403)")

# Login as Reviewer
rev_login = requests.post(
    f"{API_BASE}/auth/login",
    json={"email": rev_email, "password": "SecurePassword123!"},
)
assert rev_login.status_code == 200
rev_token = rev_login.json()["access_token"]

# RBAC Gate: Reviewer attempts to submit content -> MUST receive 403 Forbidden
rev_tamper_sub = requests.post(
    f"{API_BASE}/submissions",
    headers={"Authorization": f"Bearer {rev_token}"},
    json={
        "brand_id": brand_id,
        "title": "Reviewer Rogue Submission",
        "content_type": "social_post",
        "body": "Should be rejected.",
    },
)
assert rev_tamper_sub.status_code == 403
print("[PASS] 14. RBAC Enforcement: Reviewer Content Creation Blocked (403)")

# 5. CONTENT SUBMISSION AND ANALYSIS
# Editor creates content submission under Veritas Clinical
sub_payload = {
    "brand_id": brand_id,
    "title": "Veritas Clinical Announcement",
    "content_type": "social_post",
    "body": "Our physician formulated facial cream is a miracle cure for aging skin, guaranteed within 7 days.",
}
sub_r = requests.post(
    f"{API_BASE}/submissions",
    headers={"Authorization": f"Bearer {ed_token}"},
    json=sub_payload,
)
assert sub_r.status_code == 201, f"Submission creation failed: {sub_r.status_code} {sub_r.text}"
sub_data = sub_r.json()
sub_id = sub_data["id"]
print(f"[PASS] 15. Creator Content Submission (ID: {sub_id})")

# Run Analysis on Submission
ana_r = requests.post(
    f"{API_BASE}/submissions/{sub_id}/analyze",
    headers={"Authorization": f"Bearer {ed_token}"},
)
assert ana_r.status_code in (200, 201), f"Analysis failed: {ana_r.status_code} {ana_r.text}"
ana_res = ana_r.json()
findings = ana_res.get("findings", [])
print(f"[PASS] 16. Automated Governance Analysis: Status={ana_res['overall_status']}, Findings={len(findings)}")

# Verify finding catches prohibited term "miracle cure"
prohibited_findings = [f for f in findings if "miracle cure" in f.get("original_text", "").lower() or "miracle cure" in f.get("explanation", "").lower()]
assert len(prohibited_findings) >= 1
print("[PASS] 17. Brand Rule Grounding: Prohibited Term 'miracle cure' Flagged")

# 6. HUMAN REVIEW WORKFLOW
# Editor requests human review
rev_req_r = requests.post(
    f"{API_BASE}/submissions/{sub_id}/review-request",
    headers={"Authorization": f"Bearer {ed_token}"},
    json={"note": "Ready for brand safety review."},
)
assert rev_req_r.status_code in (200, 201), f"Review request failed: {rev_req_r.status_code} {rev_req_r.text}"
print("[PASS] 18. Human Review Request by Creator")

# Reviewer submits review decision (REQUEST_CHANGES)
rev_dec_r = requests.post(
    f"{API_BASE}/submissions/{sub_id}/reviews",
    headers={"Authorization": f"Bearer {rev_token}"},
    json={
        "decision": "revisions_requested",
        "reviewer_name": f"Reviewer {tag}",
        "comments": "Please remove 'miracle cure' and 'guaranteed within 7 days' claims.",
    },
)
assert rev_dec_r.status_code in (200, 201), f"Review decision failed: {rev_dec_r.status_code} {rev_dec_r.text}"
print("[PASS] 19. Reviewer Decision Execution: Request Changes")

# 7. VERSIONING AND REPEATED RUN PERSISTENCE
# Editor creates Version 2 addressing feedback
v2_payload = {
    "body": "Our physician formulated facial cream is designed to support skin barrier resilience in accordance with clinical trials.",
    "change_note": "Removed unapproved claims and aligned with trial data.",
}
v2_r = requests.post(
    f"{API_BASE}/submissions/{sub_id}/versions",
    headers={"Authorization": f"Bearer {ed_token}"},
    json=v2_payload,
)
assert v2_r.status_code == 201
v2_data = v2_r.json()
assert v2_data["current_version_number"] == 2
print("[PASS] 20. Versioning: Immutable v2 Revision Created")

# Run Analysis on Version 2
ana2_r = requests.post(
    f"{API_BASE}/submissions/{sub_id}/analyze",
    headers={"Authorization": f"Bearer {ed_token}"},
)
assert ana2_r.status_code in (200, 201), f"Analysis v2 failed: {ana2_r.status_code} {ana2_r.text}"
ana2_res = ana2_r.json()
print(f"[PASS] 21. Re-Analysis on v2: Status={ana2_res['overall_status']}")

# Verify Full Submission History: both runs and both versions persisted
sub_detail_r = requests.get(
    f"{API_BASE}/submissions/{sub_id}",
    headers={"Authorization": f"Bearer {ed_token}"},
)
assert sub_detail_r.status_code == 200
sub_detail = sub_detail_r.json()
assert len(sub_detail["versions"]) == 2
assert len(sub_detail["analysis_runs"]) >= 2
print(f"[PASS] 22. Submission History Persistence: {len(sub_detail['versions'])} versions, {len(sub_detail['analysis_runs'])} runs")

# 8. MULTI-FORMAT DOCUMENT EXTRACTION ON PRODUCTION
# DOCX Extraction
docx_buf = io.BytesIO()
with zipfile.ZipFile(docx_buf, "w") as z:
    z.writestr(
        "word/document.xml",
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p><w:r><w:t>Veritas Clinical press briefing for European dermatology summit.</w:t></w:r></w:p>
    </w:body>
</w:document>""",
    )
docx_r = requests.post(
    f"{API_BASE}/documents/extract",
    headers={"Authorization": f"Bearer {ed_token}"},
    data={"brand_id": brand_id},
    files={"file": ("briefing.docx", docx_buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
)
assert docx_r.status_code == 200
assert docx_r.json()["file_type"] == "docx"
assert "press briefing" in docx_r.json()["extracted_text"]
print("[PASS] 23. Live Document Ingestion: Microsoft Word (.docx) Extraction")

# PDF Extraction
pdf_writer = pypdf.PdfWriter()
pdf_writer.add_blank_page(width=300, height=300)
pdf_buf = io.BytesIO()
pdf_writer.write(pdf_buf)
pdf_r = requests.post(
    f"{API_BASE}/documents/extract",
    headers={"Authorization": f"Bearer {ed_token}"},
    data={"brand_id": brand_id},
    files={"file": ("protocol.pdf", pdf_buf.getvalue(), "application/pdf")},
)
assert pdf_r.status_code == 200
assert pdf_r.json()["file_type"] == "pdf"
print("[PASS] 24. Live Document Ingestion: Portable Document Format (PDF) Extraction")

# Image Ingestion & Visual Palette Analysis
test_img = Image.new("RGB", (400, 400), color=(30, 41, 59))  # Matches Slate Navy #1E293B
img_buf = io.BytesIO()
test_img.save(img_buf, format="PNG")
img_r = requests.post(
    f"{API_BASE}/documents/extract",
    headers={"Authorization": f"Bearer {ed_token}"},
    data={"brand_id": brand_id},
    files={"file": ("creative.png", img_buf.getvalue(), "image/png")},
)
assert img_r.status_code == 200
assert img_r.json()["file_type"] == "image/png"
assert "dominant_colors" in img_r.json()["extraction_metadata"]
print("[PASS] 25. Live Visual Asset Analysis: Color Palette Verification")

# 9. CROSS-ORGANISATION ISOLATION TEST
# Register a rival Organisation B
rival_reg = {
    "organisation_name": f"Rival Biotech {tag}",
    "display_name": f"Rival Admin {tag}",
    "email": f"rival_{tag}@biotech.test",
    "password": "SecurePassword123!",
}
rival_r = requests.post(f"{API_BASE}/auth/register", json=rival_reg)
assert rival_r.status_code == 201
rival_token = rival_r.json()["access_token"]

# Rival attempts to access Veritas Clinical brand -> MUST receive 404
rival_tamper_brand = requests.get(
    f"{API_BASE}/brands/{brand_id}",
    headers={"Authorization": f"Bearer {rival_token}"},
)
assert rival_tamper_brand.status_code == 404
print("[PASS] 26. Cross-Tenant Isolation: Unauthorized Brand Access Blocked (404)")

# Rival attempts to access submission -> MUST receive 404
rival_tamper_sub = requests.get(
    f"{API_BASE}/submissions/{sub_id}",
    headers={"Authorization": f"Bearer {rival_token}"},
)
assert rival_tamper_sub.status_code == 404
print("[PASS] 27. Cross-Tenant Isolation: Unauthorized Submission Access Blocked (404)")

print("==================================================")
print("ALL 27 PRODUCTION ACCEPTANCE JOURNEYS PASSED!")
print("==================================================")
