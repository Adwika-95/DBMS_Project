from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.database import get_db_connection

app = FastAPI(title="Medicine Information Retrieval System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/search")
def search_medicine(query: str = Query(..., min_length=1)):
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_q = query.strip()
    pattern = f"%{clean_q}%"

    # Aligned with Objective 02: Ranked partial-text search using SQL pattern matching
    sql = """
        SELECT 
            m.medicine_id,
            m.brand_name,
            m.strength,
            m.prescription_status,
            m.tablet_color,
            m.tablet_shape,
            m.strip_size,
            man.name AS manufacturer_name,
            c.category_name,
            GROUP_CONCAT(s.salt_name || ' (' || msm.composition_strength || ')', ', ') AS salts_composition,
            CASE 
                WHEN LOWER(m.brand_name) LIKE LOWER(? || '%') THEN 'Brand Name (Exact Start)'
                WHEN LOWER(s.salt_name) LIKE LOWER(? || '%') THEN 'Salt Name (Exact Start)'
                WHEN LOWER(man.name) LIKE LOWER(? || '%') THEN 'Manufacturer (Exact Start)'
                WHEN LOWER(m.brand_name) LIKE LOWER(?) THEN 'Brand Name (Fragment)'
                WHEN LOWER(s.salt_name) LIKE LOWER(?) THEN 'Salt Name (Fragment)'
                ELSE 'Manufacturer/Other (Fragment)'
            END AS match_type,
            CASE 
                WHEN LOWER(m.brand_name) LIKE LOWER(? || '%') THEN 1
                WHEN LOWER(s.salt_name) LIKE LOWER(? || '%') THEN 2
                WHEN LOWER(man.name) LIKE LOWER(? || '%') THEN 3
                ELSE 4
            END AS match_rank
        FROM Medicines m
        JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
        JOIN Categories c ON m.category_id = c.category_id
        LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
        LEFT JOIN Salts s ON msm.salt_id = s.salt_id
        WHERE m.brand_name LIKE ? OR s.salt_name LIKE ? OR man.name LIKE ?
        GROUP BY m.medicine_id
        ORDER BY match_rank ASC, m.brand_name ASC
        LIMIT 15;
    """
    
    # Passing the search term parameters for the CASE statements and WHERE clauses
    rows = cursor.execute(sql, (
        clean_q, clean_q, clean_q, pattern, pattern,  # For match_type
        clean_q, clean_q, clean_q,                    # For match_rank
        pattern, pattern, pattern                     # For WHERE clause
    )).fetchall()
    
    conn.close()
    return {"results": [dict(r) for r in rows]}
@app.get("/api/tables/{table_name}")
def get_table_data(table_name: str):
    allowed_tables = [
        "Medicines", "Manufacturers", "Salts", "Categories", 
        "Medicine_Salt_Mapping", "Batches", "Pharmacies", 
        "Pharmacy_Stock", "Users", "Search_History"
    ]
    if table_name not in allowed_tables:
        return {"error": "Invalid table name"}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    
    return {"columns": columns, "rows": [dict(r) for r in rows]}

@app.get("/api/unf")
def get_unf_data():
    """Simulates Unnormalized Form (UNF) with repeating groups for demonstration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        SELECT 
            m.brand_name AS Brand_Name,
            m.strength AS Strength,
            m.prescription_status AS Prescription_Status,
            m.tablet_color AS Tablet_Color,
            m.tablet_shape AS Tablet_Shape,
            m.strip_size AS Strip_Size,
            GROUP_CONCAT(s.salt_name || ': ' || msm.composition_strength, ' | ') AS Salts_List,
            man.name AS Manufacturer_Name,
            man.address || ', ' || man.city || ', ' || man.state AS Manufacturer_Address,
            c.category_name AS Category_Name,
            GROUP_CONCAT(b.batch_no || ' (Exp: ' || b.exp_date || ')', ' | ') AS Batches_List
        FROM Medicines m
        JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
        JOIN Categories c ON m.category_id = c.category_id
        LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
        LEFT JOIN Salts s ON msm.salt_id = s.salt_id
        LEFT JOIN Batches b ON m.medicine_id = b.medicine_id
        GROUP BY m.medicine_id;
    """
    rows = cursor.execute(sql).fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return {"columns": columns, "rows": [dict(r) for r in rows]}