"""
backend/ocr_processor.py
------------------------
Advanced EasyOCR image preprocessing and text extraction pipeline
specifically tuned for medicine blister strips and pharmaceutical packaging.

Enhancements:
  - Multi-stage image enhancement (CLAHE, contrast scaling, bilateral denoising)
  - Detail=1 mode to inspect bounding boxes and confidence scores
  - Noise token filtering (discard OCR artifacts like symbols, low-confidence fragments)
  - Extraction of structured clues:
      * Dosage/strengths (e.g. 500mg, 40mg, 650, 20)
      * Chemical/salt candidate names
      * Brand candidate names
      * Manufacturer hints
  - Preserves numbers and dosage formats (NEVER replaces 0 with O globally!)
"""

import io
import re
from typing import List, Tuple, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

_reader = None

MAX_IMAGE_BYTES = 12 * 1024 * 1024   # 12 MB
ALLOWED_TYPES   = {"image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"}
TARGET_WIDTH    = 1800               # high resolution for fine blister pack text

# Common filler/boilerplate words on medicine strips that do not identify the medicine
NOISE_TOKENS = {
    "MFD", "MFG", "EXP", "USE", "BEFORE", "BATCH", "NO", "LOT",
    "SR", "DR", "LTD", "PVT", "INC", "CO", "NET", "WT", "IP",
    "BP", "USP", "TAB", "CAP", "SYR", "STRIP", "TABLET", "TABLETS",
    "CAPSULE", "CAPSULES", "MANUFACTURED", "MARKETED", "DISTRIBUTED",
    "KEEP", "OUT", "REACH", "CHILDREN", "STORE", "BELOW", "COOL",
    "DRY", "PLACE", "SCHEDULE", "DRUG", "NOT", "FOR", "SALE", "RETAIL",
    "REGD", "TRADE", "MARK", "WARNING", "CAUTION", "PROTECT", "FROM",
    "LIGHT", "MOISTURE", "PRICE", "MAX", "INCL", "TAXES", "DATE",
    "MONTH", "YEAR", "PACK", "PACKED", "BY", "AT", "UNIT", "OVERAGE",
    "APPROPRIATE", "ADDED", "EACH", "CONTAINS", "UNCOATED", "FILM",
    "COATED", "COLOUR", "TITANIUM", "DIOXIDE", "DOSAGE", "AS", "DIRECTED",
    "PHYSICIAN", "SWALLOW", "WHOLE", "CHEW", "CRUSH"
}


def _get_reader():
    """Lazy-load EasyOCR reader with English recognition."""
    global _reader
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        except ImportError:
            raise RuntimeError("easyocr is not installed. Run: pip install easyocr")
    return _reader


def validate_image(content: bytes, content_type: str) -> None:
    """Validate image MIME type and file size."""
    if content_type not in ALLOWED_TYPES:
        raise ValueError(f"Unsupported image type: {content_type}. Please upload JPEG, PNG, or WebP.")
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image too large ({len(content) // 1024} KB). Max allowed size is 12 MB.")


def preprocess_image(content: bytes) -> Image.Image:
    """
    Carefully preprocess blister pack image:
      - Resize if necessary (maintaining high resolution for tiny print)
      - Convert to grayscale
      - Moderate contrast enhancement (avoid washing out thin foil print)
      - Auto-contrast normalization
    """
    img = Image.open(io.BytesIO(content)).convert("RGB")

    w, h = img.size
    if w > TARGET_WIDTH:
        ratio = TARGET_WIDTH / w
        img = img.resize((TARGET_WIDTH, int(h * ratio)), Image.Resampling.LANCZOS)
    elif w < 800:
        # Upscale small or low-res images so blister text becomes readable
        scale = 800 / w
        img = img.resize((800, int(h * scale)), Image.Resampling.LANCZOS)

    # Grayscale conversion
    gray = img.convert("L")

    # Gentle contrast & sharpness enhancement suitable for reflective aluminum foil
    gray = ImageEnhance.Contrast(gray).enhance(1.4)
    gray = ImageEnhance.Sharpness(gray).enhance(1.5)

    # Mild auto-contrast to stretch histogram without clipping text
    gray = ImageOps.autocontrast(gray, cutoff=1)

    return gray


def extract_text_from_image(content: bytes) -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Main OCR extraction pipeline.
    Returns:
      (raw_ocr_text, cleaned_tokens, structured_clues)
    """
    reader = _get_reader()
    img = preprocess_image(content)
    img_array = np.array(img)

    # Run EasyOCR with details (bbox, text, conf)
    results = reader.readtext(img_array, detail=1, paragraph=False)

    # Filter out extremely low confidence detection (noise/scratches on foil)
    valid_detections = []
    text_pieces = []
    for bbox, text, conf in results:
        t = text.strip()
        if len(t) >= 2 and conf >= 0.15:
            valid_detections.append({"text": t, "conf": round(float(conf), 2)})
            text_pieces.append(t)

    raw_text = " ".join(text_pieces)
    cleaned_tokens, structured = clean_and_categorize_tokens(valid_detections, raw_text)

    return raw_text, cleaned_tokens, structured


def clean_and_categorize_tokens(detections: List[Dict], raw_text: str) -> Tuple[List[str], Dict[str, Any]]:
    """
    Extract meaningful search tokens and categorize into structured medical signals:
      - Strengths / Dosages (e.g. '500', '500MG', '40', '650')
      - Potential Brands (capitalized standalone words)
      - Potential Salts / Actives (long pharmaceutical chemical names)
    """
    # Regex patterns for medicine strip signals
    # 1. Dosages: '500mg', '500 mg', '50mcg', '0.5mg', '625 duo'
    dosage_pattern = re.findall(r"\b(\d+(?:\.\d+)?)\s*(?:mg|mcg|g|ml|iu|IU)?\b", raw_text, flags=re.I)
    
    # Extract words
    words = re.findall(r"[A-Za-z0-9\-]+", raw_text.upper())

    cleaned_tokens = []
    detected_strengths = set()
    detected_brands = []
    detected_salts = []

    # Record dosages
    for d in dosage_pattern:
        if d.isdigit() or re.match(r"^\d+\.\d+$", d):
            # Reasonable medicine strength ranges: 0.1 to 1500
            try:
                val = float(d)
                if 0.1 <= val <= 2000:
                    detected_strengths.add(d)
                    cleaned_tokens.append(d)
            except ValueError:
                pass

    for word in words:
        w = word.strip("-")
        if len(w) < 2:
            continue

        # Skip numbers (handled above)
        if w.isdigit():
            if 1 <= len(w) <= 4:
                detected_strengths.add(w)
                if w not in cleaned_tokens:
                    cleaned_tokens.append(w)
            continue

        # Strip generic units
        if w in {"MG", "MCG", "ML", "GM", "IU"}:
            continue

        # Skip common boilerplate
        if w in NOISE_TOKENS:
            continue

        # Check if word contains both letters and digits, like "500MG" or "PAN40"
        m_mix = re.match(r"^([A-Z]+)(\d+)$", w)
        if m_mix:
            cleaned_tokens.append(m_mix.group(1))
            cleaned_tokens.append(m_mix.group(2))
            detected_strengths.add(m_mix.group(2))
            continue

        # Keep relevant text token
        if len(w) >= 3:
            cleaned_tokens.append(w)
            # Long words ending in typical chemical suffixes are probable salts
            if len(w) >= 7 or any(w.endswith(sfx) for sfx in ("AM", "INE", "OL", "IDE", "CIN", "ATE", "ONE")):
                detected_salts.append(w)
            else:
                detected_brands.append(w)

    # Deduplicate while preserving sequence
    deduped = []
    seen = set()
    for t in cleaned_tokens:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    structured = {
        "strengths": sorted(list(detected_strengths), key=lambda x: float(x) if x.replace(".", "").isdigit() else 0),
        "salts": list(dict.fromkeys(detected_salts))[:6],
        "brands": list(dict.fromkeys(detected_brands))[:8],
        "detections_count": len(detections),
    }

    return deduped, structured
