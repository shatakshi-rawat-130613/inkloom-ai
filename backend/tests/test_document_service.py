"""Tests for PDF document extraction, text ingestion, and visual brand analysis."""

import io
from PIL import Image
import pypdf
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import BrandProfile
from app.services.document_service import (
    analyze_image_visual_compliance,
    extract_pdf_content,
    extract_text_content,
)


@pytest.fixture
def client(seeded_db):
    """TestClient sharing the seeded test database."""
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _create_sample_pdf_bytes(text: str) -> bytes:
    """Helper to generate a valid in-memory PDF."""
    writer = pypdf.PdfWriter()
    # Add a blank page and annotate or write directly
    page = writer.add_blank_page(width=300, height=300)
    # pypdf can create a clean PDF file structure
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _create_sample_image_bytes(color: tuple[int, int, int] = (253, 251, 247), size=(400, 400)) -> bytes:
    """Helper to generate an in-memory test PNG image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_text_content():
    content = "LumaCare Daily Hydrating Cream supports clearer-looking skin without harsh chemicals."
    extracted, meta = extract_text_content(content.encode("utf-8"), "press_release.txt")
    assert extracted == content
    assert meta["word_count"] == 10
    assert meta["character_count"] == len(content)


def test_extract_pdf_content():
    pdf_bytes = _create_sample_pdf_bytes("Dummy")
    extracted, meta = extract_pdf_content(pdf_bytes, "sample.pdf")
    assert meta["page_count"] == 1
    assert "is_encrypted" in meta
    assert meta["is_encrypted"] is False


def test_visual_image_compliant_palette(seeded_db):
    # Brand asset palette for LumaCare includes Ivory (253, 251, 247)
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").first()
    img_bytes = _create_sample_image_bytes(color=(253, 251, 247), size=(500, 500))

    extracted_text, meta, findings = analyze_image_visual_compliance(
        img_bytes, "product_banner.png", brand_assets=brand.assets
    )

    assert meta["width_px"] == 500
    assert meta["height_px"] == 500
    assert len(meta["dominant_colors"]) > 0
    # No divergent palette warnings
    palette_findings = [f for f in findings if "color" in f.explanation.lower()]
    assert len(palette_findings) == 0


def test_visual_image_divergent_palette(seeded_db):
    # Neon Magenta (255, 0, 255) is not in LumaCare's warm, realistic palette
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").first()
    img_bytes = _create_sample_image_bytes(color=(255, 0, 255), size=(500, 500))

    extracted_text, meta, findings = analyze_image_visual_compliance(
        img_bytes, "neon_promo.png", brand_assets=brand.assets
    )

    palette_findings = [f for f in findings if "color" in f.explanation.lower()]
    assert len(palette_findings) >= 1
    assert palette_findings[0].source.value == "visual"
    assert "diverges from the approved brand color palette" in palette_findings[0].explanation


def test_document_extraction_endpoint(client, seeded_db):
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").first()
    txt_content = b"LumaCare morning ritual: gentle cleansing followed by our soothing facial cream."

    res = client.post(
        "/api/documents/extract",
        data={"brand_id": str(brand.id)},
        files={"file": ("routine.txt", txt_content, "text/plain")},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["file_name"] == "routine.txt"
    assert data["extraction_source"] == "document"
    assert "gentle cleansing" in data["extracted_text"]
    assert data["file_size_bytes"] == len(txt_content)


def test_extract_docx_content_and_endpoint(client, seeded_db):
    import zipfile

    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").first()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "word/document.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p><w:r><w:t>LumaCare official press release for spring 2026.</w:t></w:r></w:p>
        <w:p><w:r><w:t>Formulated with nourishing botanical extracts.</w:t></w:r></w:p>
    </w:body>
</w:document>""",
        )

    docx_bytes = buf.getvalue()
    res = client.post(
        "/api/documents/extract",
        data={"brand_id": str(brand.id)},
        files={"file": ("spring_release.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["file_name"] == "spring_release.docx"
    assert data["file_type"] == "docx"
    assert "official press release" in data["extracted_text"]
    assert data["extraction_metadata"]["paragraph_count"] == 2


def test_perceptual_hashing_and_logo_verification(seeded_db):
    from PIL import ImageDraw
    from app.models import BrandAsset
    from app.services.document_service import (
        compute_perceptual_hash,
        hamming_distance,
        verify_logo_reference,
    )

    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").first()
    # Create a reference logo image with a distinct mark and record its perceptual hash
    logo_img = Image.new("RGB", (300, 100), color=(253, 251, 247))
    d1 = ImageDraw.Draw(logo_img)
    d1.rectangle([50, 20, 250, 80], fill=(28, 25, 23))
    ref_hash = compute_perceptual_hash(logo_img)

    logo_asset = BrandAsset(
        brand_id=brand.id,
        asset_type="logo",
        name="LumaCare Test Logo",
        asset_metadata={"perceptual_hash": ref_hash, "text": "LumaCare"},
    )
    seeded_db.add(logo_asset)
    seeded_db.commit()

    # 1. Matching logo image bytes
    buf_matching = io.BytesIO()
    logo_img.save(buf_matching, format="PNG")
    status, conf, exp, finding = verify_logo_reference(
        buf_matching.getvalue(), "matching_logo.png", "LumaCare", [logo_asset]
    )
    assert status == "approved_logo_detected"
    assert finding is None

    # 2. Promotional banner creative with different visual layout
    banner_img = Image.new("RGB", (800, 250), color=(253, 251, 247))
    d2 = ImageDraw.Draw(banner_img)
    d2.ellipse([50, 10, 150, 200], fill=(59, 94, 79))
    buf_banner = io.BytesIO()
    banner_img.save(buf_banner, format="PNG")
    b_status, b_conf, b_exp, b_finding = verify_logo_reference(
        buf_banner.getvalue(), "promo_banner.png", "LumaCare", [logo_asset]
    )
    assert b_status in {"expected_logo_not_detected", "possible_incorrect_logo"}
    assert b_finding is not None
    assert b_finding.source.value == "visual"
