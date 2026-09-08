import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "medicine_system.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, "r") as f:
        cursor.executescript(f.read())

    manufacturers = [
        ("Sun Pharma Industries", "Sun House, Goregaon", "Mumbai", "Maharashtra"),
        ("Cipla Ltd", "Cipla House, Peninsula Business Park", "Mumbai", "Maharashtra"),
        ("Dr. Reddy's Laboratories", "7-1-27 Ameerpet", "Hyderabad", "Telangana"),
        ("Abbott India", "Godrej BKC", "Mumbai", "Maharashtra"),
        ("Mankind Pharma", "Okhla Phase III", "New Delhi", "Delhi")
    ]
    cursor.executemany("INSERT OR IGNORE INTO Manufacturers (name, address, city, state) VALUES (?, ?, ?, ?)", manufacturers)

    categories = [
        ("Analgesic & Antipyretic",), ("Antibiotic",), ("Antacid & Anti-ulcer",),
        ("Antiallergic",), ("Antihypertensive",), ("Antidiabetic",)
    ]
    cursor.executemany("INSERT OR IGNORE INTO Categories (category_name) VALUES (?)", categories)

    salts = [
        ("Paracetamol",), ("Amoxicillin",), ("Potassium Clavulanate",),
        ("Pantoprazole",), ("Cetirizine",), ("Telmisartan",)
    ]
    cursor.executemany("INSERT OR IGNORE INTO Salts (salt_name) VALUES (?)", salts)

    meds = [
        ("Dolo 650", "650mg", "OTC", "White", "Capsule-shaped", "15 Tablets", 1, 1, [(1, "650mg")]),
        ("Augmentin 625", "625mg", "Rx", "White", "Oblong", "10 Tablets", 2, 2, [(2, "500mg"), (3, "125mg")]),
        ("Pan 40", "40mg", "Rx", "Yellow", "Round", "15 Tablets", 3, 3, [(4, "40mg")]),
        ("Cetzine", "10mg", "OTC", "White", "Round", "10 Tablets", 2, 4, [(5, "10mg")]),
        ("Telma 40", "40mg", "Rx", "Orange", "Round", "30 Tablets", 1, 5, [(6, "40mg")])
    ]

    for brand, strength, rx, color, shape, strip, m_id, c_id, salt_maps in meds:
        cursor.execute("""
            INSERT INTO Medicines (brand_name, strength, prescription_status, tablet_color, tablet_shape, strip_size, manufacturer_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (brand, strength, rx, color, shape, strip, m_id, c_id))
        med_id = cursor.lastrowid
        
        for salt_id, comp in salt_maps:
            cursor.execute("""
                INSERT OR IGNORE INTO Medicine_Salt_Mapping (medicine_id, salt_id, composition_strength)
                VALUES (?, ?, ?)
            """, (med_id, salt_id, comp))

        cursor.execute("""
            INSERT OR IGNORE INTO Batches (medicine_id, batch_no, mfg_date, exp_date)
            VALUES (?, ?, ?, ?)
        """, (med_id, f"BT{1000 + med_id}", "2025-01-10", "2027-12-31"))

    pharmacies = [
        ("Apollo Pharmacy - Main", "12 GST Road", 12.8230, 80.0440, "+91 9840112233"),
        ("MedPlus Pharmacy", "45 Kelambakkam Rd", 12.8390, 80.1550, "+91 9840445566")
    ]
    cursor.executemany("INSERT OR IGNORE INTO Pharmacies (name, address, latitude, longitude, contact) VALUES (?, ?, ?, ?, ?)", pharmacies)

    for med_id in range(1, 6):
        cursor.execute("INSERT OR IGNORE INTO Pharmacy_Stock (pharmacy_id, medicine_id, price, quantity) VALUES (1, ?, ?, ?)", (med_id, 35.0, 100))
        cursor.execute("INSERT OR IGNORE INTO Pharmacy_Stock (pharmacy_id, medicine_id, price, quantity) VALUES (2, ?, ?, ?)", (med_id, 32.0, 50))

    cursor.execute("INSERT OR IGNORE INTO Users (name, email) VALUES ('Adwika', 'adwika@example.com'), ('Richika', 'richika@example.com')")
    conn.commit()
    conn.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed()