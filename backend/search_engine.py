"""
backend/search_engine.py
------------------------
Multi-signal medicine search and ranking engine with Fuzzy Matching.

Features:
  - Multi-signal scoring across Brand, Chemical Salt, Dosage/Strength, and Manufacturer
  - Fuzzy string matching (SequenceMatcher) to gracefully recover OCR typos on torn/reflective strips
    (e.g., 'LRVIPIL' / 'LEVIPI' -> 'Levipil', 'EVETIRACETAMM' -> 'Levetiracetam')
  - Full candidate evaluation (no premature cutoff / LIMIT before scoring)
  - Detailed diagnostic clue generation explaining exact match provenance
  - Generic same-salt alternatives query
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict, Any
from backend.database import get_db_connection

# Anchor score for 100% confidence (e.g. Salt match 35 + Brand match 30 + Strength 20 = 85)
_MAX_ANCHOR_SCORE = 75

CONF_HIGH   = 70   # "Strong match — verified signals"
CONF_MEDIUM = 40   # "Probable match"
CONF_LOW    = 15   # "Weak match — verify with doctor/pharmacist"


def _norm(s: str) -> str:
    """Normalize string: uppercase and strip excess spaces."""
    return (s or "").upper().strip()


def _fuzzy_sim(a: str, b: str) -> float:
    """Calculate SequenceMatcher similarity between two strings."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _strength_numeric(s: str) -> str:
    """Extract numeric dosage component: '500 mg' -> '500', '0.5mg' -> '0.5'"""
    m = re.search(r"(\d+(?:\.\d+)?)", s or "")
    return m.group(1) if m else ""


def _score_one_medicine(row: Dict, tokens: List[str]) -> Dict[str, Any]:
    """
    Score a single medicine against search tokens using multi-signal & fuzzy criteria.
    """
    score = 0
    matched_clues: List[Dict] = []

    brand_raw = row.get("brand_name", "")
    brand     = _norm(brand_raw)
    # Brand base word (e.g. 'Levipil 500' -> 'LEVIPIL')
    brand_base = brand.split()[0] if brand else ""

    mfg       = _norm(row.get("manufacturer_name", ""))
    mfg_short = _norm(row.get("manufacturer_short", ""))
    salts     = _norm(row.get("salts_composition", "") or "")
    strength  = _norm(row.get("strength", ""))
    str_num   = _strength_numeric(strength)
    generic   = _norm(row.get("generic_name", "") or "")
    ocr_hints = _norm(row.get("ocr_hints", "") or "")
    pkg_kw    = _norm(row.get("packaging_keywords", "") or "")

    for token in tokens:
        tok = token.upper().strip()
        if not tok:
            continue

        token_scored = False

        # ── 1. ACTIVE SALT / COMPOSITION MATCH (Highest diagnostic weight) ────
        # Exact substring match in composition or generic name
        if len(tok) >= 4 and (tok in salts or tok in generic):
            score += 35
            token_scored = True
            matched_clues.append({
                "token": tok,
                "field": "salt",
                "pts": 35,
                "label": f'"{tok}" -> Active Ingredient match'
            })
        else:
            # Fuzzy match on individual salt names
            # e.g. 'EVETIRACETAMM' vs 'LEVETIRACETAM'
            for salt_segment in re.split(r"[,+()]", salts):
                clean_salt = re.sub(r"\d+\s*MG|\d+", "", salt_segment).strip()
                if len(clean_salt) >= 5 and len(tok) >= 5:
                    sim = _fuzzy_sim(tok, clean_salt)
                    if sim >= 0.82:
                        score += 30
                        token_scored = True
                        matched_clues.append({
                            "token": tok,
                            "field": "salt_fuzzy",
                            "pts": 30,
                            "label": f'"{tok}" -> Active Ingredient similarity ({int(sim*100)}% match with {clean_salt.title()})'
                        })
                        break

        # ── 2. BRAND NAME MATCH ──────────────────────────────────────────────
        if tok == brand or tok == brand_base:
            score += 35
            token_scored = True
            matched_clues.append({
                "token": tok,
                "field": "brand_name",
                "pts": 35,
                "label": f'"{tok}" -> Brand exact match'
            })
        elif len(tok) >= 3 and (brand.startswith(tok) or brand_base.startswith(tok)):
            score += 25
            token_scored = True
            matched_clues.append({
                "token": tok,
                "field": "brand_name",
                "pts": 25,
                "label": f'"{tok}" -> Brand prefix ({brand_raw})'
            })
        elif len(tok) >= 4 and tok in brand:
            score += 18
            token_scored = True
            matched_clues.append({
                "token": tok,
                "field": "brand_name",
                "pts": 18,
                "label": f'"{tok}" -> Brand fragment ({brand_raw})'
            })
        elif len(tok) >= 4 and len(brand_base) >= 4:
            # Fuzzy Brand Match (handles OCR letter swaps like LRVIPIL -> LEVIPIL)
            sim = _fuzzy_sim(tok, brand_base)
            if sim >= 0.78:
                pts = int(28 * sim)
                score += pts
                token_scored = True
                matched_clues.append({
                    "token": tok,
                    "field": "brand_fuzzy",
                    "pts": pts,
                    "label": f'"{tok}" -> Brand similarity ({int(sim*100)}% match with {brand_raw})'
                })

        # ── 3. STRENGTH / DOSAGE MATCH ───────────────────────────────────────
        if tok == strength or (str_num and tok == str_num):
            score += 20
            token_scored = True
            matched_clues.append({
                "token": tok,
                "field": "strength",
                "pts": 20,
                "label": f'"{tok}" -> Exact Dosage match ({strength})'
            })

        # ── 4. MANUFACTURER MATCH ────────────────────────────────────────────
        if len(tok) >= 3:
            if (mfg_short and tok == mfg_short) or (mfg and tok in mfg.split()):
                score += 15
                token_scored = True
                matched_clues.append({
                    "token": tok,
                    "field": "manufacturer",
                    "pts": 15,
                    "label": f'"{tok}" -> Manufacturer match ({row.get("manufacturer_name")})'
                })
            elif (tok in mfg or tok in mfg_short) and len(tok) >= 4:
                score += 10
                token_scored = True
                matched_clues.append({
                    "token": tok,
                    "field": "manufacturer",
                    "pts": 10,
                    "label": f'"{tok}" -> Manufacturer hint'
                })

        # ── 5. OCR KEYWORD HINTS / PACKAGING ─────────────────────────────────
        if len(tok) >= 3 and (tok in ocr_hints or tok in pkg_kw):
            score += 8
            matched_clues.append({
                "token": tok,
                "field": "ocr_hints",
                "pts": 8,
                "label": f'"{tok}" -> Packaging keyword match'
            })

    # Deduplicate clues: keep highest-scoring clue per field
    deduped = []
    seen_fields = set()
    # Sort clues by points descending
    matched_clues.sort(key=lambda c: -c["pts"])
    for clue in matched_clues:
        key = (clue["token"], clue["field"])
        if key not in seen_fields:
            seen_fields.add(key)
            deduped.append(clue)

    # Calculate confidence percentage
    confidence_pct = min(100, round(score * 100 / _MAX_ANCHOR_SCORE))

    if confidence_pct >= CONF_HIGH:
        confidence_label = "Strong match"
    elif confidence_pct >= CONF_MEDIUM:
        confidence_label = "Probable match"
    else:
        confidence_label = "Low confidence"

    return {
        "score": score,
        "confidence_pct": confidence_pct,
        "confidence_label": confidence_label,
        "matched_clues": deduped,
    }


def search_medicines(tokens: List[str], limit: int = 15) -> List[Dict[str, Any]]:
    """
    Search and rank medicines using multi-signal scoring and fuzzy matching.
    """
    if not tokens:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve active medicines with all relevant metadata
    # The medicine catalog is fast to scan and score in memory
    sql = """
        SELECT
            m.medicine_id,
            m.brand_name,
            m.generic_name,
            m.strength,
            m.dosage_form,
            m.prescription_status,
            m.tablet_color,
            m.tablet_shape,
            m.strip_size,
            m.uses,
            m.warnings,
            m.storage_info,
            man.name AS manufacturer_name,
            man.short_name AS manufacturer_short,
            c.category_name,
            GROUP_CONCAT(DISTINCT s.salt_name || ' (' || msm.composition_strength || ')') AS salts_composition,
            pd.dominant_color,
            pd.packaging_keywords,
            GROUP_CONCAT(DISTINCT ok.keyword) AS ocr_hints
        FROM Medicines m
        JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
        JOIN Categories c ON m.category_id = c.category_id
        LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
        LEFT JOIN Salts s ON msm.salt_id = s.salt_id
        LEFT JOIN Packaging_Details pd ON m.medicine_id = pd.medicine_id
        LEFT JOIN OCR_Keywords ok ON m.medicine_id = ok.medicine_id
        WHERE m.is_active = 1
        GROUP BY m.medicine_id
    """
    rows = cursor.execute(sql).fetchall()
    conn.close()

    candidates = []
    for r in rows:
        d = dict(r)
        score_data = _score_one_medicine(d, tokens)
        if score_data["score"] > 0:
            d.update(score_data)
            candidates.append(d)

    # Sort descending by score, then brand name
    candidates.sort(key=lambda x: (-x["score"], -x["confidence_pct"], x["brand_name"]))

    return candidates[:limit]


def get_alternatives(medicine_id: int) -> List[Dict[str, Any]]:
    """
    Find bio-equivalent or same active-ingredient medicines.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT DISTINCT
            m.medicine_id,
            m.brand_name,
            m.strength,
            m.dosage_form,
            m.prescription_status,
            man.name AS manufacturer_name,
            c.category_name,
            GROUP_CONCAT(DISTINCT s.salt_name || ' (' || msm2.composition_strength || ')') AS salts_composition,
            GROUP_CONCAT(DISTINCT s.salt_name) AS shared_salts
        FROM Medicine_Salt_Mapping msm1
        JOIN Salts s ON msm1.salt_id = s.salt_id
        JOIN Medicine_Salt_Mapping msm2 ON msm2.salt_id = msm1.salt_id AND msm2.medicine_id != ?
        JOIN Medicines m ON msm2.medicine_id = m.medicine_id
        JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
        JOIN Categories c ON m.category_id = c.category_id
        WHERE msm1.medicine_id = ?
          AND m.is_active = 1
        GROUP BY m.medicine_id
        ORDER BY m.brand_name
    """
    rows = cursor.execute(sql, (medicine_id, medicine_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
