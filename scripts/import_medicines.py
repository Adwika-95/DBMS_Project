"""
import_medicines.py
-------------------
Data ingestion pipeline for the Medicine Information Retrieval System.

Pipeline:
  raw CSV files
      ↓  normalize
      ↓  validate
      ↓  deduplicate
      ↓  insert/update SQLite DB

Run from project root:
    python scripts/import_medicines.py
"""

import csv
import os
import sqlite3
import re
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH   = os.path.join(BASE_DIR, "medicine_system.db")
SCHEMA_V2 = os.path.join(BASE_DIR, "schema_v2.sql")
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")

MANUFACTURERS_CSV = os.path.join(RAW_DIR, "manufacturers_raw.csv")
SALTS_CSV         = os.path.join(RAW_DIR, "salts_raw.csv")
MEDICINES_CSV     = os.path.join(RAW_DIR, "medicines_raw.csv")

COLLECTED_DATE = str(date.today())

# ── helpers ──────────────────────────────────────────────────────────────────

def normalize_name(s: str) -> str:
    """Strip excess whitespace and title-case."""
    return " ".join(s.strip().split())

def normalize_strength(s: str) -> str:
    """Lowercase units, remove spaces between number and unit."""
    s = s.strip()
    s = re.sub(r"(\d)\s+(mg|mcg|g|ml|%|IU|iu)", lambda m: m.group(1) + m.group(2).lower(), s, flags=re.I)
    return s

def get_or_insert(cursor, table: str, pk_col: str, lookup_col: str, value: str, extra: dict = None):
    """Return id of existing row or insert and return new id."""
    row = cursor.execute(f"SELECT {pk_col} FROM {table} WHERE {lookup_col} = ?", (value,)).fetchone()
    if row:
        return row[0]
    cols = [lookup_col]
    vals = [value]
    if extra:
        cols += list(extra.keys())
        vals += list(extra.values())
    placeholders = ", ".join("?" * len(cols))
    cursor.execute(
        f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
        vals
    )
    # fetch again (handles UNIQUE conflict)
    row = cursor.execute(f"SELECT {pk_col} FROM {table} WHERE {lookup_col} = ?", (value,)).fetchone()
    return row[0] if row else None

# ── import manufacturers ──────────────────────────────────────────────────────

def import_manufacturers(cursor):
    inserted = skipped = 0
    with open(MANUFACTURERS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = normalize_name(row["name"])
            existing = cursor.execute(
                "SELECT manufacturer_id FROM Manufacturers WHERE name = ?", (name,)
            ).fetchone()
            if existing:
                skipped += 1
                continue
            cursor.execute("""
                INSERT OR IGNORE INTO Manufacturers
                    (name, short_name, address, city, state, country, website)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                row.get("short_name", "").strip() or None,
                row.get("address", "").strip() or None,
                row.get("city", "").strip() or None,
                row.get("state", "").strip() or None,
                row.get("country", "India").strip(),
                row.get("website", "").strip() or None,
            ))
            inserted += 1
    print(f"  Manufacturers: {inserted} inserted, {skipped} skipped (already exist)")

# ── import salts ──────────────────────────────────────────────────────────────

def import_salts(cursor):
    inserted = skipped = 0
    with open(SALTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            salt_name = normalize_name(row["salt_name"])
            # Skip combination placeholders (they are just labels in the CSV)
            if not salt_name or "Combination" in row.get("drug_class", ""):
                continue
            existing = cursor.execute(
                "SELECT salt_id FROM Salts WHERE salt_name = ?", (salt_name,)
            ).fetchone()
            if existing:
                skipped += 1
                continue
            cursor.execute("""
                INSERT OR IGNORE INTO Salts (salt_name, iupac_name, drug_class)
                VALUES (?, ?, ?)
            """, (
                salt_name,
                row.get("iupac_name", "").strip() or None,
                row.get("drug_class", "").strip() or None,
            ))
            inserted += 1
    print(f"  Salts: {inserted} inserted, {skipped} skipped")

# ── import medicines ──────────────────────────────────────────────────────────

def import_medicines(cursor):
    inserted = skipped = errors = 0
    with open(MEDICINES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            brand_name  = normalize_name(row["brand_name"])
            strength    = normalize_strength(row.get("strength", ""))
            mfg_name    = normalize_name(row["manufacturer"])
            cat_name    = normalize_name(row["category"])
            salts_str   = row.get("salts", "").strip()

            # ── resolve manufacturer ──
            mfg_row = cursor.execute(
                "SELECT manufacturer_id FROM Manufacturers WHERE name = ?", (mfg_name,)
            ).fetchone()
            if not mfg_row:
                # try inserting a minimal record
                cursor.execute(
                    "INSERT OR IGNORE INTO Manufacturers(name) VALUES (?)", (mfg_name,)
                )
                mfg_row = cursor.execute(
                    "SELECT manufacturer_id FROM Manufacturers WHERE name = ?", (mfg_name,)
                ).fetchone()
            if not mfg_row:
                print(f"  [ERROR] Could not resolve manufacturer '{mfg_name}' for {brand_name}")
                errors += 1
                continue
            mfg_id = mfg_row[0]

            # ── resolve category ──
            cat_id = get_or_insert(cursor, "Categories", "category_id", "category_name", cat_name)

            # ── check duplicate ──
            existing = cursor.execute(
                "SELECT medicine_id FROM Medicines WHERE brand_name=? AND strength=? AND manufacturer_id=?",
                (brand_name, strength, mfg_id)
            ).fetchone()
            if existing:
                skipped += 1
                continue

            # ── insert medicine ──
            cursor.execute("""
                INSERT INTO Medicines
                    (brand_name, generic_name, strength, dosage_form, prescription_status,
                     tablet_color, tablet_shape, strip_size, uses, warnings, storage_info,
                     manufacturer_id, category_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                brand_name,
                row.get("generic_name", "").strip() or None,
                strength,
                row.get("dosage_form", "").strip() or None,
                row.get("prescription_status", "OTC").strip(),
                row.get("tablet_color", "").strip() or None,
                row.get("tablet_shape", "").strip() or None,
                row.get("strip_size", "").strip() or None,
                row.get("uses", "").strip() or None,
                row.get("warnings", "").strip() or None,
                row.get("storage_info", "").strip() or None,
                mfg_id,
                cat_id,
            ))
            med_id = cursor.lastrowid

            # ── insert salt mappings ──
            if salts_str:
                for salt_entry in salts_str.split(","):
                    # parse "Salt Name Xmg" or "Salt Name"
                    salt_entry = salt_entry.strip()
                    m = re.match(r"^(.+?)\s+([\d.]+\s*(?:mg|mcg|g|IU|%|iu))\s*$", salt_entry, re.I)
                    if m:
                        sname = normalize_name(m.group(1))
                        comp_strength = normalize_strength(m.group(2))
                    else:
                        sname = normalize_name(salt_entry)
                        comp_strength = None

                    if not sname:
                        continue
                    salt_id = get_or_insert(cursor, "Salts", "salt_id", "salt_name", sname)
                    if salt_id:
                        cursor.execute("""
                            INSERT OR IGNORE INTO Medicine_Salt_Mapping
                                (medicine_id, salt_id, composition_strength)
                            VALUES (?, ?, ?)
                        """, (med_id, salt_id, comp_strength))

            # ── packaging metadata ──
            dominant_color   = row.get("dominant_color", "").strip() or None
            pack_keywords    = row.get("packaging_keywords", "").strip() or None
            if dominant_color or pack_keywords:
                # parse strip_count from strip_size
                strip_size_str = row.get("strip_size", "")
                sc_match = re.search(r"(\d+)", strip_size_str)
                strip_count = int(sc_match.group(1)) if sc_match else None

                cursor.execute("""
                    INSERT OR IGNORE INTO Packaging_Details
                        (medicine_id, dominant_color, strip_count, packaging_keywords, packaging_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    med_id,
                    dominant_color,
                    strip_count,
                    pack_keywords,
                    row.get("dosage_form", "").strip() or None,
                ))

            # ── source provenance ──
            src_name = row.get("source_name", "").strip() or None
            src_type = row.get("source_type", "manual").strip()
            if src_name:
                cursor.execute("""
                    INSERT INTO Medicine_Sources
                        (medicine_id, source_name, source_type, date_collected, verification_status)
                    VALUES (?, ?, ?, ?, 'unverified')
                """, (med_id, src_name, src_type, COLLECTED_DATE))

            inserted += 1

    print(f"  Medicines: {inserted} inserted, {skipped} skipped (duplicates), {errors} errors")

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Medicine Information Retrieval System — Data Import")
    print("=" * 60)

    # Fresh DB from schema_v2
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old DB: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")

    print(f"\nApplying schema_v2.sql …")
    with open(SCHEMA_V2, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    print("  Schema applied.")

    print("\nImporting data …")
    import_manufacturers(cursor)
    import_salts(cursor)
    import_medicines(cursor)

    # ── seed demo users ──
    cursor.execute("""
        INSERT OR IGNORE INTO Users (name, email, role)
        VALUES ('Richika (Admin)', 'richika@example.com', 'admin'),
               ('Adwika', 'adwika@example.com', 'user')
    """)

    # ── seed demo pharmacies ──
    cursor.executemany("""
        INSERT OR IGNORE INTO Pharmacies (name, address, city, latitude, longitude, contact)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ("Apollo Pharmacy – Guindy", "12 GST Road Guindy", "Chennai", 12.8230, 80.0440, "+91 9840112233"),
        ("MedPlus – Velachery", "45 Velachery Main Road", "Chennai", 12.9780, 80.2200, "+91 9840445566"),
        ("Netmeds Pharmacy – Andheri", "Link Road Andheri West", "Mumbai", 19.1196, 72.8361, "+91 9820334455"),
    ])

    conn.commit()

    # ── summary ──
    print("\nDatabase summary:")
    for table in ["Manufacturers", "Categories", "Salts", "Medicines",
                  "Medicine_Salt_Mapping", "Packaging_Details",
                  "OCR_Keywords", "Medicine_Sources", "Users", "Pharmacies"]:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<28} {count:>4} rows")

    conn.close()
    print("\nImport complete. DB saved to:", DB_PATH)

if __name__ == "__main__":
    main()
