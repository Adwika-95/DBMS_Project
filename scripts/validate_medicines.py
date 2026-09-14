"""
validate_medicines.py
---------------------
QA / validation script for the medicine_system.db.

Run from project root:
    python scripts/validate_medicines.py
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "medicine_system.db")

def check(conn):
    c = conn.cursor()
    issues = []

    # 1. Medicines with no salt mapping
    rows = c.execute("""
        SELECT m.medicine_id, m.brand_name
        FROM Medicines m
        LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
        WHERE msm.medicine_id IS NULL AND m.is_active = 1
    """).fetchall()
    if rows:
        issues.append(f"[WARN] {len(rows)} medicines with NO salt mapping:")
        for r in rows[:10]:
            issues.append(f"      ID={r[0]} {r[1]}")

    # 2. Medicines with missing dosage_form
    count = c.execute("SELECT COUNT(*) FROM Medicines WHERE dosage_form IS NULL AND is_active=1").fetchone()[0]
    if count:
        issues.append(f"[WARN] {count} medicines missing dosage_form")

    # 3. Duplicate brand+strength+mfg
    rows = c.execute("""
        SELECT brand_name, strength, manufacturer_id, COUNT(*) AS cnt
        FROM Medicines
        GROUP BY brand_name, strength, manufacturer_id
        HAVING cnt > 1
    """).fetchall()
    if rows:
        issues.append(f"[ERROR] {len(rows)} duplicate brand+strength+manufacturer combos found!")
        for r in rows:
            issues.append(f"      {r[0]} {r[1]} (mfg_id={r[2]}) — {r[3]} times")

    # 4. Orphaned salt mappings
    count = c.execute("""
        SELECT COUNT(*) FROM Medicine_Salt_Mapping msm
        WHERE NOT EXISTS (SELECT 1 FROM Medicines m WHERE m.medicine_id = msm.medicine_id)
    """).fetchone()[0]
    if count:
        issues.append(f"[ERROR] {count} orphaned Medicine_Salt_Mapping rows")

    # 5. Medicine_Sources coverage
    total  = c.execute("SELECT COUNT(*) FROM Medicines").fetchone()[0]
    w_src  = c.execute("SELECT COUNT(DISTINCT medicine_id) FROM Medicine_Sources").fetchone()[0]
    no_src = total - w_src
    if no_src:
        issues.append(f"[WARN] {no_src}/{total} medicines have no source/provenance record")

    # 6. OCR keyword auto-trigger check
    with_kw = c.execute("SELECT COUNT(DISTINCT medicine_id) FROM OCR_Keywords").fetchone()[0]
    if with_kw < total:
        issues.append(f"[INFO] {with_kw}/{total} medicines have OCR keywords (trigger may not have fired for all)")

    # ── Summary ──
    print("=" * 60)
    print("Validation Report")
    print("=" * 60)

    counts = [
        ("Manufacturers",       "SELECT COUNT(*) FROM Manufacturers"),
        ("Categories",          "SELECT COUNT(*) FROM Categories"),
        ("Salts",               "SELECT COUNT(*) FROM Salts"),
        ("Medicines (total)",   "SELECT COUNT(*) FROM Medicines"),
        ("Medicines (active)",  "SELECT COUNT(*) FROM Medicines WHERE is_active=1"),
        ("Salt mappings",       "SELECT COUNT(*) FROM Medicine_Salt_Mapping"),
        ("Packaging details",   "SELECT COUNT(*) FROM Packaging_Details"),
        ("OCR keywords",        "SELECT COUNT(*) FROM OCR_Keywords"),
        ("Medicine sources",    "SELECT COUNT(*) FROM Medicine_Sources"),
        ("Users",               "SELECT COUNT(*) FROM Users"),
        ("Pharmacies",          "SELECT COUNT(*) FROM Pharmacies"),
    ]
    for label, sql in counts:
        n = c.execute(sql).fetchone()[0]
        print(f"  {label:<28} {n:>4}")

    print()
    if issues:
        for msg in issues:
            print(msg)
    else:
        print("  All checks passed. No issues found.")

    print("=" * 60)

    # ── Top 5 manufacturers by medicine count ──
    print("\nTop manufacturers by medicine count:")
    rows = c.execute("""
        SELECT man.name, COUNT(m.medicine_id) AS cnt
        FROM Manufacturers man
        LEFT JOIN Medicines m ON man.manufacturer_id = m.manufacturer_id
        GROUP BY man.manufacturer_id
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(f"  {r[0]:<40}  {r[1]} medicines")

    # ── Most common salts ──
    print("\nMost common active ingredients:")
    rows = c.execute("""
        SELECT s.salt_name, COUNT(msm.medicine_id) AS cnt
        FROM Salts s
        JOIN Medicine_Salt_Mapping msm ON s.salt_id = msm.salt_id
        GROUP BY s.salt_id
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()
    for r in rows:
        print(f"  {r[0]:<40}  in {r[1]} medicines")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}. Run import_medicines.py first.")
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        check(conn)
        conn.close()
