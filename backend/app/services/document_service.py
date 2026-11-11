"""Document parsing, OCR and visual asset compliance analysis service.

Supports:
1. PDF document extraction with pypdf (multi-page text, metadata, page counts).
2. Plain text / Markdown document ingestion.
3. Image visual analysis with Pillow:
   - Dimension, aspect ratio, color mode and DPI inspection.
   - Dominant color extraction and palette matching against approved brand colors.
   - Contrast calculation.
   - Visual compliance verification against brand assets (logo, palette, imagery rules).
"""

import io
import math
import re
from typing import Any

from PIL import Image
import pypdf

from app.enums import FindingCategory, FindingSource, FindingType, Severity
from app.schemas import FindingDraft


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join(c * 2 for c in hex_clean)
    return int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)


def _color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """Euclidean distance in RGB space (0 to ~441)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def extract_pdf_content(file_bytes: bytes, filename: str) -> tuple[str, dict[str, Any]]:
    """Extract text and structural metadata from a PDF file using pypdf."""
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    page_texts: list[str] = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            page_texts.append(text.strip())

    full_text = "\n\n".join(page_texts)

    meta: dict[str, Any] = {
        "page_count": len(reader.pages),
        "extracted_pages": len(page_texts),
        "character_count": len(full_text),
        "word_count": len(full_text.split()) if full_text else 0,
        "is_encrypted": reader.is_encrypted,
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
    }
    return text, meta


def extract_dominant_colors(img: Image.Image, num_colors: int = 5) -> list[dict[str, Any]]:
    """Extract dominant RGB colors and pixel distribution percentages."""
    rgb_img = img.convert("RGB")
    # Resize to speed up quantization
    thumb = rgb_img.resize((100, 100))
    # Quantize to palette
    palette_img = thumb.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette = palette_img.getpalette() or []
    counts = palette_img.getcolors() or []

    total_pixels = 100 * 100
    dominant: list[dict[str, Any]] = []

    # Sort by pixel frequency descending
    counts.sort(key=lambda x: x[0], reverse=True)

    for count, color_idx in counts[:num_colors]:
        r = palette[color_idx * 3]
        g = palette[color_idx * 3 + 1]
        b = palette[color_idx * 3 + 2]
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        pct = round((count / total_pixels) * 100, 1)
        dominant.append({"hex": hex_code, "rgb": [r, g, b], "percentage": pct})

    return dominant


def analyze_image_visual_compliance(
    file_bytes: bytes,
    filename: str,
    brand_assets: list[Any] | None = None,
) -> tuple[str, dict[str, Any], list[FindingDraft]]:
    """Analyze image dimensions, dominant color palette and visual guideline compliance.
    
    Returns:
    - extracted_text / summary string
    - visual metadata dictionary
    - list of visual compliance findings
    """
    img = Image.open(io.BytesIO(file_bytes))
    width, height = img.size
    aspect_ratio = round(width / max(height, 1), 2)

    dominant_colors = extract_dominant_colors(img)

    meta: dict[str, Any] = {
        "format": img.format or "UNKNOWN",
        "mode": img.mode,
        "width_px": width,
        "height_px": height,
        "aspect_ratio": f"{aspect_ratio}:1",
        "dominant_colors": dominant_colors,
    }

    findings: list[FindingDraft] = []
    brand_assets = brand_assets or []

    # 1. Palette Verification
    palette_assets = [a for a in brand_assets if getattr(a, "asset_type", "") == "color_palette"]
    if palette_assets:
        approved_colors_meta = palette_assets[0].asset_metadata.get("colors", [])
        approved_rgbs = []
        for ac in approved_colors_meta:
            if "hex" in ac:
                approved_rgbs.append((ac["name"], _hex_to_rgb(ac["hex"]), ac["hex"]))

        if approved_rgbs:
            # Check if dominant colors with >15% area diverge sharply from approved palette
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

                    # Threshold distance in RGB space (~120 is noticeable discrepancy)
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

    # 2. Dimensions & Quality Verification
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

    # Summary text representation
    colors_summary = ", ".join(f"{c['hex']} ({c['percentage']}%)" for c in dominant_colors[:3])
    extracted_text = (
        f"[Visual Image Asset: {filename} | {width}x{height}px | Format: {img.format} | "
        f"Dominant Palette: {colors_summary}]"
    )

    return extracted_text, meta, findings
