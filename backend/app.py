"""
backend/app.py
--------------
Medicine Information Retrieval System — FastAPI backend

Routes:
  GET  /api/search                  Partial-text search (multi-token)
  POST /api/ocr                     Image upload → OCR → search
  GET  /api/medicine/{id}           Full medicine detail
  GET  /api/alternatives/{id}       Same-composition medicines
  GET  /api/tables/{table_name}     EER table explorer
  GET  /api/unf                     UNF flat view (normalization demo)
  GET  /api/views/{view_name}       SQL view explorer
  GET  /api/dbstats                 Database statistics

Auth routes:
  GET  /api/auth/google             Redirect to Google OAuth
  GET  /api/auth/callback           OAuth callback
  POST /api/auth/logout             (client-side: just delete token)
  GET  /api/auth/me                 Current user info

Admin routes (require admin JWT):
  GET  /api/admin/medicines         List all medicines
  POST /api/admin/medicines         Add medicine
  PUT  /api/admin/medicines/{id}    Edit medicine
  DELETE /api/admin/medicines/{id}  Deactivate medicine
  POST /api/admin/manufacturers     Add manufacturer
  POST /api/admin/salts             Add salt
"""

import os
from typing import Optional, List

from fastapi import (
    FastAPI, Query, UploadFile, File, HTTPException,
    Depends, Header, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.auth import (
    get_google_auth_url, exchange_code_for_user, upsert_google_user,
    create_jwt, get_current_user, require_user, require_admin,
    FRONTEND_BASE, GOOGLE_CLIENT_ID,
)
from backend.search_engine import search_medicines, get_alternatives

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Medicine Information Retrieval System API",
    description="DBMS Project — Partial strip medicine identification",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helper ────────────────────────────────────────────────────────────────────

def _log_search(query_text: str, mode: str, top_match_id, top_match_score, result_count, user=None):
    """Write to Search_History table."""
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO Search_History
                (user_id, query_text, search_mode, top_match_id, top_match_score, result_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user["user_id"] if user else None,
            query_text[:500],
            mode,
            top_match_id,
            top_match_score,
            result_count,
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass  # never let logging crash a search

# ── 1. Text Search ────────────────────────────────────────────────────────────

@app.get("/api/search")
def search_medicine(
    query: str = Query(..., min_length=1, description="Partial text to search"),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Multi-token partial text search.
    Splits the query into tokens and scores medicines against all signals.
    """
    tokens = [t.strip().upper() for t in query.split() if len(t.strip()) >= 2]
    if not tokens:
        return {"results": [], "tokens": [], "query": query}

    results = search_medicines(tokens)

    # Log search
    top = results[0] if results else None
    _log_search(
        query_text=query, mode="text",
        top_match_id=top["medicine_id"] if top else None,
        top_match_score=top["confidence_pct"] if top else None,
        result_count=len(results),
        user=current_user,
    )

    # Safety: add disclaimer when confidence is low
    disclaimer = None
    if not results or results[0]["confidence_pct"] < 40:
        disclaimer = (
            "⚠️ Match confidence is low. "
            "Please verify this medicine with a registered pharmacist or doctor before taking it."
        )

    return {
        "query": query,
        "tokens": tokens,
        "results": results,
        "disclaimer": disclaimer,
    }

# ── 2. OCR Upload ─────────────────────────────────────────────────────────────

@app.post("/api/ocr")
async def ocr_search(
    file: UploadFile = File(...),
    extra_text: str = Query("", description="Optional extra text typed by user"),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Upload a medicine strip image.
    OCR extracts text tokens, combined with optional manually typed text.
    Returns scored medicine matches.
    """
    # Lazy import so the app starts without EasyOCR loaded
    from backend.ocr_processor import validate_image, extract_text_from_image

    content      = await file.read()
    content_type = file.content_type or "image/jpeg"

    try:
        validate_image(content, content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        raw_text, ocr_tokens, structured = extract_text_from_image(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    # Merge OCR tokens with manually typed extra text
    extra_tokens = [t.strip().upper() for t in re.findall(r"[A-Za-z0-9\-]+", extra_text)] if extra_text.strip() else []
    all_tokens   = list(dict.fromkeys(ocr_tokens + extra_tokens))  # deduplicate, preserve order

    if not all_tokens:
        return {
            "raw_ocr_text": raw_text,
            "ocr_tokens": ocr_tokens,
            "extra_tokens": extra_tokens,
            "all_tokens": [],
            "structured_signals": structured,
            "results": [],
            "disclaimer": "No clear medicine clues could be extracted. Try adjusting the photo angle or lighting.",
        }

    results = search_medicines(all_tokens)

    top = results[0] if results else None
    _log_search(
        query_text=f"[OCR] {' '.join(all_tokens[:8])}",
        mode="ocr" if not extra_text.strip() else "combined",
        top_match_id=top["medicine_id"] if top else None,
        top_match_score=top["confidence_pct"] if top else None,
        result_count=len(results),
        user=current_user,
    )

    disclaimer = None
    if not results or results[0]["confidence_pct"] < 40:
        disclaimer = (
            "Verification Advisory: Match confidence is low. Please verify this medicine packaging with a registered doctor or pharmacist."
        )

    return {
        "raw_ocr_text": raw_text,
        "ocr_tokens": ocr_tokens,
        "extra_tokens": extra_tokens,
        "all_tokens": all_tokens,
        "structured_signals": structured,
        "results": results,
        "disclaimer": disclaimer,
    }

# ── 3. Medicine Detail ────────────────────────────────────────────────────────

@app.get("/api/medicine/{medicine_id}")
def get_medicine_detail(medicine_id: int):
    """Full medicine information page."""
    conn   = get_db_connection()
    cursor = conn.cursor()
    row    = cursor.execute(
        "SELECT * FROM v_medicine_full WHERE medicine_id = ?", (medicine_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Medicine not found")
    result = dict(row)

    # Fetch source provenance
    sources = cursor.execute(
        "SELECT * FROM Medicine_Sources WHERE medicine_id = ?", (medicine_id,)
    ).fetchall()
    result["sources"] = [dict(s) for s in sources]

    # Fetch batch info (most recent 3)
    batches = cursor.execute(
        "SELECT batch_no, mfg_date, exp_date FROM Batches WHERE medicine_id = ? ORDER BY exp_date DESC LIMIT 3",
        (medicine_id,)
    ).fetchall()
    result["batches"] = [dict(b) for b in batches]

    conn.close()
    return result

# ── 4. Alternative Medicines ──────────────────────────────────────────────────

@app.get("/api/alternatives/{medicine_id}")
def get_alternative_medicines(medicine_id: int):
    """
    Find medicines sharing at least one active ingredient with the given medicine.
    Demonstrates: Medicine → Salt → Medicine relational join.
    """
    conn   = get_db_connection()
    cursor = conn.cursor()
    exists = cursor.execute("SELECT 1 FROM Medicines WHERE medicine_id=?", (medicine_id,)).fetchone()
    conn.close()
    if not exists:
        raise HTTPException(status_code=404, detail="Medicine not found")

    alternatives = get_alternatives(medicine_id)
    return {
        "medicine_id": medicine_id,
        "alternatives": alternatives,
        "note": "These are same-composition products. They are NOT a recommendation to switch medication. Always consult your doctor or pharmacist.",
    }

# ── 5. EER Table Explorer ─────────────────────────────────────────────────────

ALLOWED_TABLES = [
    "Medicines", "Manufacturers", "Salts", "Categories",
    "Medicine_Salt_Mapping", "Batches", "Pharmacies",
    "Pharmacy_Stock", "Users", "Search_History",
    "Packaging_Details", "OCR_Keywords", "Medicine_Sources",
]

@app.get("/api/tables/{table_name}")
def get_table_data(table_name: str):
    """Browse any normalized table (EER explorer)."""
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Table '{table_name}' not accessible")
    conn    = get_db_connection()
    cursor  = conn.cursor()
    rows    = cursor.execute(f"SELECT * FROM {table_name} LIMIT 200").fetchall()
    columns = [d[0] for d in cursor.description]
    conn.close()
    return {"table": table_name, "columns": columns, "rows": [dict(r) for r in rows]}

# ── 6. UNF View (Normalization Demo) ─────────────────────────────────────────

@app.get("/api/unf")
def get_unf_data():
    """Unnormalized flat view for normalization demonstration."""
    conn   = get_db_connection()
    cursor = conn.cursor()
    rows   = cursor.execute("SELECT * FROM v_unf_flat LIMIT 100").fetchall()
    columns = [d[0] for d in cursor.description]
    conn.close()
    return {"columns": columns, "rows": [dict(r) for r in rows]}

# ── 7. SQL Views Explorer ─────────────────────────────────────────────────────

ALLOWED_VIEWS = {
    "v_medicine_full":      "Full medicine info (all joins)",
    "v_unf_flat":           "UNF flat view (1NF violation demo)",
    "v_search_stats":       "Most searched medicines",
    "v_same_composition":   "Same-composition medicines",
    "v_manufacturer_stats": "Manufacturer statistics",
}

@app.get("/api/views")
def list_views():
    return {"views": [{"name": k, "description": v} for k, v in ALLOWED_VIEWS.items()]}

@app.get("/api/views/{view_name}")
def get_view_data(view_name: str):
    if view_name not in ALLOWED_VIEWS:
        raise HTTPException(status_code=400, detail="View not accessible")
    conn    = get_db_connection()
    cursor  = conn.cursor()
    rows    = cursor.execute(f"SELECT * FROM {view_name} LIMIT 100").fetchall()
    columns = [d[0] for d in cursor.description]
    conn.close()
    return {
        "view": view_name,
        "description": ALLOWED_VIEWS[view_name],
        "columns": columns,
        "rows": [dict(r) for r in rows],
    }

# ── 8. DB Statistics ──────────────────────────────────────────────────────────

@app.get("/api/dbstats")
def get_db_stats():
    conn   = get_db_connection()
    cursor = conn.cursor()
    stats  = {}
    for table in ALLOWED_TABLES + list(ALLOWED_VIEWS.keys()):
        try:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = count
        except Exception:
            pass
    # Most searched
    top_searches = cursor.execute("""
        SELECT query_text, COUNT(*) AS cnt
        FROM Search_History
        GROUP BY LOWER(query_text)
        ORDER BY cnt DESC
        LIMIT 5
    """).fetchall()
    conn.close()
    return {
        "table_counts": stats,
        "top_searches": [dict(r) for r in top_searches],
    }

# ── 9. Auth — Google OAuth ────────────────────────────────────────────────────

@app.get("/api/auth/google")
def login_google():
    """Redirect browser to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars."
        )
    return RedirectResponse(url=get_google_auth_url())

@app.get("/api/auth/callback")
def google_callback(code: str = Query(...)):
    """Handle OAuth callback, issue JWT, redirect to frontend."""
    try:
        google_info = exchange_code_for_user(code)
        user        = upsert_google_user(google_info)
        jwt_token   = create_jwt({
            "user_id":  user["user_id"],
            "email":    user["email"],
            "name":     user["name"],
            "role":     user.get("role", "user"),
            "avatar":   user.get("avatar_url", ""),
        })
        # Redirect to frontend with token in URL fragment
        return RedirectResponse(url=f"{FRONTEND_BASE}/#token={jwt_token}")
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_BASE}/#auth_error={str(e)[:100]}")

@app.get("/api/auth/me")
def get_me(current_user: Optional[dict] = Depends(get_current_user)):
    """Return current user info from JWT or null."""
    if not current_user:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": current_user}

# ── 10. Admin Routes ──────────────────────────────────────────────────────────

class MedicineIn(BaseModel):
    brand_name:          str
    generic_name:        Optional[str] = None
    strength:            str
    dosage_form:         Optional[str] = None
    prescription_status: str = "OTC"
    tablet_color:        Optional[str] = None
    tablet_shape:        Optional[str] = None
    strip_size:          Optional[str] = None
    uses:                Optional[str] = None
    warnings:            Optional[str] = None
    storage_info:        Optional[str] = None
    manufacturer_id:     int
    category_id:         int
    salt_ids:            List[int] = []

class ManufacturerIn(BaseModel):
    name:        str
    short_name:  Optional[str] = None
    address:     Optional[str] = None
    city:        Optional[str] = None
    state:       Optional[str] = None
    website:     Optional[str] = None

class SaltIn(BaseModel):
    salt_name:  str
    drug_class: Optional[str] = None

@app.get("/api/admin/medicines")
def admin_list_medicines(admin=Depends(require_admin)):
    conn    = get_db_connection()
    cursor  = conn.cursor()
    rows    = cursor.execute("SELECT * FROM v_medicine_full ORDER BY brand_name").fetchall()
    columns = [d[0] for d in cursor.description]
    conn.close()
    return {"columns": columns, "rows": [dict(r) for r in rows]}

@app.post("/api/admin/medicines", status_code=201)
def admin_add_medicine(med: MedicineIn, admin=Depends(require_admin)):
    conn   = get_db_connection()
    cursor = conn.cursor()
    # Check duplicate
    existing = cursor.execute(
        "SELECT medicine_id FROM Medicines WHERE brand_name=? AND strength=? AND manufacturer_id=?",
        (med.brand_name, med.strength, med.manufacturer_id)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Medicine already exists with this brand/strength/manufacturer")
    cursor.execute("""
        INSERT INTO Medicines
            (brand_name, generic_name, strength, dosage_form, prescription_status,
             tablet_color, tablet_shape, strip_size, uses, warnings, storage_info,
             manufacturer_id, category_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        med.brand_name, med.generic_name, med.strength, med.dosage_form,
        med.prescription_status, med.tablet_color, med.tablet_shape, med.strip_size,
        med.uses, med.warnings, med.storage_info, med.manufacturer_id, med.category_id,
    ))
    med_id = cursor.lastrowid
    for salt_id in med.salt_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO Medicine_Salt_Mapping(medicine_id, salt_id) VALUES(?,?)",
            (med_id, salt_id)
        )
    conn.commit()
    conn.close()
    return {"medicine_id": med_id, "message": "Medicine added"}

@app.put("/api/admin/medicines/{medicine_id}")
def admin_edit_medicine(medicine_id: int, med: MedicineIn, admin=Depends(require_admin)):
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Medicines SET
            brand_name=?, generic_name=?, strength=?, dosage_form=?,
            prescription_status=?, tablet_color=?, tablet_shape=?, strip_size=?,
            uses=?, warnings=?, storage_info=?, manufacturer_id=?, category_id=?
        WHERE medicine_id=?
    """, (
        med.brand_name, med.generic_name, med.strength, med.dosage_form,
        med.prescription_status, med.tablet_color, med.tablet_shape, med.strip_size,
        med.uses, med.warnings, med.storage_info, med.manufacturer_id, med.category_id,
        medicine_id,
    ))
    conn.commit()
    conn.close()
    return {"message": "Medicine updated"}

@app.delete("/api/admin/medicines/{medicine_id}")
def admin_deactivate_medicine(medicine_id: int, admin=Depends(require_admin)):
    conn = get_db_connection()
    conn.execute("UPDATE Medicines SET is_active=0 WHERE medicine_id=?", (medicine_id,))
    conn.commit()
    conn.close()
    return {"message": "Medicine deactivated"}

@app.get("/api/admin/manufacturers")
def admin_list_manufacturers(admin=Depends(require_admin)):
    conn   = get_db_connection()
    rows   = conn.execute("SELECT * FROM Manufacturers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/admin/manufacturers", status_code=201)
def admin_add_manufacturer(mfg: ManufacturerIn, admin=Depends(require_admin)):
    conn   = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Manufacturers(name, short_name, address, city, state, website)
            VALUES(?,?,?,?,?,?)
        """, (mfg.name, mfg.short_name, mfg.address, mfg.city, mfg.state, mfg.website))
        mid = cursor.lastrowid
        conn.commit()
        return {"manufacturer_id": mid, "message": "Manufacturer added"}
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    finally:
        conn.close()

@app.get("/api/admin/salts")
def admin_list_salts(admin=Depends(require_admin)):
    conn  = get_db_connection()
    rows  = conn.execute("SELECT * FROM Salts ORDER BY salt_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/admin/salts", status_code=201)
def admin_add_salt(salt: SaltIn, admin=Depends(require_admin)):
    conn   = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Salts(salt_name, drug_class) VALUES(?,?)",
            (salt.salt_name, salt.drug_class)
        )
        sid = cursor.lastrowid
        conn.commit()
        return {"salt_id": sid, "message": "Salt added"}
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    finally:
        conn.close()

@app.get("/api/admin/categories")
def admin_list_categories(admin=Depends(require_admin)):
    conn  = get_db_connection()
    rows  = conn.execute("SELECT * FROM Categories ORDER BY category_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/admin/stats")
def admin_stats(admin=Depends(require_admin)):
    """Admin dashboard statistics."""
    conn   = get_db_connection()
    cursor = conn.cursor()
    stats = {
        "total_medicines":     cursor.execute("SELECT COUNT(*) FROM Medicines WHERE is_active=1").fetchone()[0],
        "total_inactive":      cursor.execute("SELECT COUNT(*) FROM Medicines WHERE is_active=0").fetchone()[0],
        "total_manufacturers": cursor.execute("SELECT COUNT(*) FROM Manufacturers").fetchone()[0],
        "total_salts":         cursor.execute("SELECT COUNT(*) FROM Salts").fetchone()[0],
        "total_searches":      cursor.execute("SELECT COUNT(*) FROM Search_History").fetchone()[0],
        "searches_today":      cursor.execute(
            "SELECT COUNT(*) FROM Search_History WHERE DATE(search_timestamp) = DATE('now')"
        ).fetchone()[0],
        "recent_searches": [dict(r) for r in cursor.execute("""
            SELECT sh.query_text, sh.search_mode, sh.top_match_score,
                   sh.result_count, sh.search_timestamp, u.name AS user_name
            FROM Search_History sh
            LEFT JOIN Users u ON sh.user_id = u.user_id
            ORDER BY sh.search_timestamp DESC LIMIT 10
        """).fetchall()],
    }
    conn.close()
    return stats