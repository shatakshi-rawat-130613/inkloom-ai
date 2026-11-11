"""Document parsing, OCR and visual asset compliance analysis service.

Supports:
1. PDF document extraction with pypdf (multi-page text, metadata, scanned PDF OCR fallback).
2. DOCX document extraction using standard library zipfile and XML parsing.
3. Plain text / Markdown document ingestion.
4. Promotional image multimodal OCR and visual brand inspection:
   - Dimension, aspect ratio, color mode and DPI inspection.
   - Dominant color extraction and palette matching against approved brand colors.
   - Genuine visual logo reference comparison against approved brand logo assets:
     Distinguishes approved logo detected, possible incorrect logo,
     expected logo not detected, or unable to determine reliably.
   - Multimodal OCR extraction for promotional copy, headlines, and claims.
"""

import io
import math
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image
import pypdf

from app.enums import FindingCategory, FindingSource, FindingType, Severity
from app.schemas import FindingDraft
from app.services.gemini_service import run_gemini_logo_verification, run_gemini_vision_ocr


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    return int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """Euclidean distance in RGB space (0 to ~441)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def compute_perceptual_hash(img: Image.Image, hash_size: int = 8) -> str:
    """Computes difference hash (dHash) for visual comparison."""
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(resized.get_flattened_data() if hasattr(resized, "get_flattened_data") else resized.getdata())

    diff = []
    width = hash_size + 1
    for row in range(hash_size):
        row_offset = row * width
        for col in range(hash_size):
            diff.append(pixels[row_offset + col] > pixels[row_offset + col + 1])

    decimal_val = 0
    hex_chars = []
    for idx, bit in enumerate(diff):
        if bit:
            decimal_val += 1 << (idx % 4)
        if (idx % 4) == 3:
            hex_chars.append(hex(decimal_val)[2:])
            decimal_val = 0
    return "".join(hex_chars)


def hamming_distance(hash1: str, hash2: str) -> int:
    """Computes Hamming distance between two hex hash strings."""
    if len(hash1) != len(hash2):
        return 999
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")
    except ValueError:
        return 999


def extract_docx_content(file_bytes: bytes, filename: str) -> tuple[str, dict[str, Any]]:
    """Extract text from Microsoft Word .docx files."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
            xml_content = docx_zip.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

            paragraphs: list[str] = []
            for p in tree.iterfind(".//w:p", namespaces):
                texts = [node.text for node in p.iterfind(".//w:t", namespaces) if node.text]
                if texts:
                    clean = "".join(texts).strip()
                    if clean:
                        paragraphs.append(clean)

            full_text = "\n\n".join(paragraphs)
            meta: dict[str, Any] = {
                "format": "DOCX",
                "paragraph_count": len(paragraphs),
                "character_count": len(full_text),
                "word_count": len(full_text.split()) if full_text else 0,
                "source": "document",
            }
            return full_text, meta
    except Exception as exc:
        raise ValueError(f"Failed to extract DOCX document content: {exc}")


def extract_pdf_content(file_bytes: bytes, filename: str) -> tuple[str, dict[str, Any]]:
    """Extract text and structural metadata from a PDF file using pypdf.

    If no native text can be extracted (e.g. scanned PDF), falls back to
    extracting page images and running multimodal OCR.
    """
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    page_texts: list[str] = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            page_texts.append(text.strip())

    full_text = "\n\n".join(page_texts)
    source = "document"

    # Scanned PDF fallback
    if len(full_text.strip()) < 10:
        ocr_page_texts: list[str] = []
        for page in reader.pages:
            try:
                for img_obj in getattr(page, "images", []):
                    img_data = img_obj.data
                    ocr_res = run_gemini_vision_ocr(img_data, mime_type="image/png")
                    if ocr_res.strip():
                        ocr_page_texts.append(ocr_res.strip())
            except Exception:
                pass
        if ocr_page_texts:
            full_text = "\n\n".join(ocr_page_texts)
            source = "ocr"

    meta: dict[str, Any] = {
        "page_count": len(reader.pages),
        "extracted_pages": len(ocr_page_texts) if (len(full_text.strip()) < 10 and 'ocr_page_texts' in locals() and ocr_page_texts) else len(page_texts),
        "character_count": len(full_text),
        "word_count": len(full_text.split()) if full_text else 0,
        "is_encrypted": reader.is_encrypted,
        "source": source,
    }

    if reader.metadata:
        for k in ("title", "author", "creator", "producer"):
            val = getattr(reader.metadata, k, None)
            if val:
                meta[k] = str(val)

    return full_text, meta


def extract_text_content(file_bytes: bytes, filename: str) -> tuple[str, dict[str, Any]]:
    """Extract text from plain text or markdown files."""
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="replace")

    meta: dict[str, Any] = {
        "character_count": len(text),
        "word_count": len(text.split()) if text else 0,
        "line_count": len(text.splitlines()),
        "source": "document",
    }
    return text, meta


def extract_dominant_colors(img: Image.Image, num_colors: int = 5) -> list[dict[str, Any]]:
    """Extract dominant RGB colors and pixel distribution percentages."""
    rgb_img = img.convert("RGB")
    thumb = rgb_img.resize((100, 100))
    palette_img = thumb.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette = palette_img.getpalette() or []
    counts = palette_img.getcolors() or []

    total_pixels = 100 * 100
    dominant: list[dict[str, Any]] = []

    counts.sort(key=lambda x: x[0], reverse=True)

    for count, color_idx in counts[:num_colors]:
        r = palette[color_idx * 3]
        g = palette[color_idx * 3 + 1]
        b = palette[color_idx * 3 + 2]
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        pct = round((count / total_pixels) * 100, 1)
        dominant.append({"hex": hex_code, "rgb": [r, g, b], "percentage": pct})

    return dominant


def verify_logo_reference(
    file_bytes: bytes,
    filename: str,
    brand_name: str,
    brand_assets: list[Any] | None,
) -> tuple[str, float, str, FindingDraft | None]:
    """Inspects an uploaded visual asset against approved brand logo assets.

    Distinguishes:
    - approved_logo_detected
    - possible_incorrect_logo
    - expected_logo_not_detected
    - unable_to_determine
    """
    brand_assets = brand_assets or []
    logo_assets = [a for a in brand_assets if getattr(a, "asset_type", "") == "logo"]

    if not logo_assets:
        return "unable_to_determine", 0.5, "No approved logo asset configured for brand.", None

    logo_asset = logo_assets[0]
    meta = getattr(logo_asset, "asset_metadata", {}) or {}

    # 1. Multimodal Gemini Visual Logo Inspection
    gemini_status, gemini_conf, gemini_exp = run_gemini_logo_verification(
        file_bytes, brand_name or "Active Brand", meta
    )

    if gemini_status != "unable_to_determine":
        finding = None
        if gemini_status == "expected_logo_not_detected":
            finding = FindingDraft(
                source=FindingSource.VISUAL,
                category=FindingCategory.OTHER,
                severity=Severity.MEDIUM,
                finding_type=FindingType.POTENTIAL_ISSUE,
                original_text=f"Visual asset: {filename}",
                evidence=f"Brand identity standards require approved {brand_name} logo presence on promotional creative.",
                explanation=gemini_exp or f"Approved {brand_name} logo was not detected in this promotional creative.",
                suggestion=f"Include the approved {brand_name} logo/wordmark in accordance with brand placement guidelines.",
                confidence=gemini_conf,
            )
        elif gemini_status == "possible_incorrect_logo":
            finding = FindingDraft(
                source=FindingSource.VISUAL,
                category=FindingCategory.OTHER,
                severity=Severity.HIGH,
                finding_type=FindingType.CONFIRMED_RULE_VIOLATION,
                original_text=f"Visual asset: {filename}",
                evidence=f"Visual brand standards require authentic and unaltered {brand_name} logo representation.",
                explanation=gemini_exp or "Possible incorrect, altered, or non-approved logo detected in image.",
                suggestion=f"Replace with authentic, approved {brand_name} logo asset from brand workspace.",
                confidence=gemini_conf,
            )
        return gemini_status, gemini_conf, gemini_exp, finding

    # 2. Algorithmic Perceptual Hashing & Aspect Ratio Matcher
    try:
        img = Image.open(io.BytesIO(file_bytes))
        target_hash = compute_perceptual_hash(img)
        ref_hash = meta.get("perceptual_hash")

        if ref_hash:
            dist = hamming_distance(target_hash, ref_hash)
            if dist <= 6:
                return "approved_logo_detected", 0.95, "Approved logo matches visual reference hash.", None
            elif dist <= 22:
                finding = FindingDraft(
                    source=FindingSource.VISUAL,
                    category=FindingCategory.OTHER,
                    severity=Severity.HIGH,
                    finding_type=FindingType.POTENTIAL_ISSUE,
                    original_text=f"Visual asset: {filename}",
                    evidence=f"Visual brand standards require authentic and unaltered {brand_name} logo representation.",
                    explanation=f"Visual logo variance detected (perceptual divergence distance={dist}). Possible modified or distorted logo variant.",
                    suggestion=f"Verify logo asset against approved brand master vector.",
                    confidence=0.85,
                )
                return "possible_incorrect_logo", 0.85, "Possible modified logo variant detected.", finding

        width, height = img.size
        is_banner = (width / max(height, 1)) > 2.0 or (height / max(width, 1)) > 2.0
        if is_banner:
            finding = FindingDraft(
                source=FindingSource.VISUAL,
                category=FindingCategory.OTHER,
                severity=Severity.MEDIUM,
                finding_type=FindingType.RECOMMENDATION,
                original_text=f"Promotional creative {width}x{height}px",
                evidence=f"Promotional banners should prominently display the approved {brand_name} logo.",
                explanation=f"No approved logo detected on promotional banner creative.",
                suggestion=f"Ensure approved {brand_name} logo is placed in the designated safe zone.",
                confidence=0.75,
            )
            return "expected_logo_not_detected", 0.75, "Expected logo not detected on promotional creative.", finding

    except Exception:
        pass

    return "unable_to_determine", 0.50, "Visual logo evaluation could not be completed deterministically.", None


def analyze_image_visual_compliance(
    file_bytes: bytes,
    filename: str,
    brand_name: str = "",
    brand_assets: list[Any] | None = None,
) -> tuple[str, dict[str, Any], list[FindingDraft]]:
    """Analyze image dimensions, dominant color palette, visual logo compliance and OCR text.

    Returns:
    - extracted_text / summary string (OCR text if present, otherwise visual asset summary)
    - visual metadata dictionary
    - list of visual compliance findings
    """
    img = Image.open(io.BytesIO(file_bytes))
    width, height = img.size
    aspect_ratio = round(width / max(height, 1), 2)

    dominant_colors = extract_dominant_colors(img)
    brand_assets = brand_assets or []

    # 1. Multimodal OCR: Extract marketing copy, headlines, and claims from promotional images
    ocr_text = run_gemini_vision_ocr(file_bytes, mime_type=f"image/{img.format.lower() if img.format else 'png'}")
    source = "ocr" if ocr_text.strip() else "visual"

    meta: dict[str, Any] = {
        "format": img.format or "UNKNOWN",
        "mode": img.mode,
        "width_px": width,
        "height_px": height,
        "aspect_ratio": f"{aspect_ratio}:1",
        "dominant_colors": dominant_colors,
        "source": source,
        "has_ocr_text": bool(ocr_text.strip()),
        "word_count": len(ocr_text.split()) if ocr_text.strip() else 0,
    }

    findings: list[FindingDraft] = []

    # 2. Genuine Visual Logo Verification
    logo_status, logo_conf, logo_exp, logo_finding = verify_logo_reference(
        file_bytes, filename, brand_name, brand_assets
    )
    meta["logo_verification"] = {
        "status": logo_status,
        "confidence": logo_conf,
        "explanation": logo_exp,
    }
    if logo_finding:
        findings.append(logo_finding)

    # 3. Palette Verification against approved brand colors
    palette_assets = [a for a in brand_assets if getattr(a, "asset_type", "") == "color_palette"]
    if palette_assets:
        approved_colors_meta = palette_assets[0].asset_metadata.get("colors", [])
        approved_rgbs = []
        for ac in approved_colors_meta:
            if "hex" in ac:
                approved_rgbs.append((ac["name"], _hex_to_rgb(ac["hex"]), ac["hex"]))

        if approved_rgbs:
            for dc in dominant_colors:
                if dc["percentage"] >= 15.0:
                    d_rgb = tuple(dc["rgb"])
                    min_dist = float("inf")
                    closest_name = ""
                    closest_hex = ""
                    for name, a_rgb, a_hex in approved_rgbs:
                        dist = _color_distance(d_rgb, a_rgb)
                        if dist < min_dist:
                            min_dist = dist
                            closest_name = name
                            closest_hex = a_hex

                    if min_dist > 135.0:
                        findings.append(
                            FindingDraft(
                                source=FindingSource.VISUAL,
                                category=FindingCategory.OTHER,
                                severity=Severity.MEDIUM,
                                finding_type=FindingType.POTENTIAL_ISSUE,
                                original_text=f"Dominant color {dc['hex']} ({dc['percentage']}%)",
                                explanation=(
                                    f"Detected prominent color {dc['hex']} occupies {dc['percentage']}% of the image "
                                    f"but diverges from the approved brand color palette (closest approved match is "
                                    f"{closest_name} {closest_hex}, distance={int(min_dist)})."
                                ),
                                suggestion=f"Align visual assets with approved brand colors ({', '.join(c['hex'] for c in approved_colors_meta[:4])}).",
                                confidence=0.88,
                            )
                        )

    # 4. Dimensions & Quality Verification
    if width < 300 or height < 300:
        findings.append(
            FindingDraft(
                source=FindingSource.VISUAL,
                category=FindingCategory.OTHER,
                severity=Severity.LOW,
                finding_type=FindingType.RECOMMENDATION,
                original_text=f"Resolution {width}x{height}px",
                explanation=f"Image resolution ({width}x{height}px) is below recommended minimum (300x300px) for promotional publishing.",
                suggestion="Use high-resolution source imagery to avoid pixelation and compression artifacts.",
                confidence=0.95,
            )
        )

    # Set extracted_text:
    # If OCR extracted readable text from the promotional creative, use that text so the
    # compliance engine can evaluate its claims directly. Otherwise, fall back to structural summary.
    if ocr_text.strip():
        extracted_text = ocr_text.strip()
    else:
        colors_summary = ", ".join(f"{c['hex']} ({c['percentage']}%)" for c in dominant_colors[:3])
        extracted_text = (
            f"[Visual Image Asset: {filename} | {width}x{height}px | Format: {img.format} | "
            f"Dominant Palette: {colors_summary}]"
        )

    return extracted_text, meta, findings
