import sqlite3

conn = sqlite3.connect('medicine_system.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print('=== TABLES ===')
for t in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {t['name']}").fetchone()[0]
    print(f"  {t['name']}: {count} rows")

print()
print('=== MEDICINES ===')
rows = cursor.execute('''
    SELECT m.medicine_id, m.brand_name, m.strength, man.name as mfg, c.category_name,
           m.tablet_color, m.tablet_shape, m.strip_size, m.prescription_status
    FROM Medicines m
    JOIN Manufacturers man ON m.manufacturer_id=man.manufacturer_id
    JOIN Categories c ON m.category_id=c.category_id
''').fetchall()
for r in rows:
    print(f"  [{r['medicine_id']}] {r['brand_name']} {r['strength']} | {r['mfg']} | {r['category_name']} | {r['tablet_color']}, {r['tablet_shape']}")

print()
print('=== SALTS ===')
rows = cursor.execute("SELECT * FROM Salts").fetchall()
for r in rows:
    print(f"  {dict(r)}")

print()
print('=== MANUFACTURERS ===')
rows = cursor.execute("SELECT * FROM Manufacturers").fetchall()
for r in rows:
    print(f"  {dict(r)}")

print()
print('=== MEDICINE_SALT_MAPPING ===')
rows = cursor.execute("""
    SELECT m.brand_name, s.salt_name, msm.composition_strength
    FROM Medicine_Salt_Mapping msm
    JOIN Medicines m ON msm.medicine_id = m.medicine_id
    JOIN Salts s ON msm.salt_id = s.salt_id
""").fetchall()
for r in rows:
    print(f"  {r['brand_name']} -> {r['salt_name']} ({r['composition_strength']})")

print()
print('=== BATCHES ===')
rows = cursor.execute("SELECT * FROM Batches").fetchall()
for r in rows:
    print(f"  {dict(r)}")

print()
print('=== SCHEMA DETAILS ===')
for t in tables:
    print(f"\n--- {t['name']} ---")
    info = cursor.execute(f"PRAGMA table_info({t['name']})").fetchall()
    for col in info:
        print(f"  {col['name']} {col['type']} {'NOT NULL' if col['notnull'] else ''} {'PK' if col['pk'] else ''}")

conn.close()
