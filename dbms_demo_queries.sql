-- ============================================================
-- DBMS Viva / Demo SQL Queries
-- Medicine Information Retrieval System
-- ============================================================
-- Run these in any SQLite tool (DB Browser, sqlite3 CLI, etc.)
-- after applying schema_v2.sql and running import pipeline.
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- Q1. Find all medicines containing a particular salt
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: JOIN, WHERE, GROUP_CONCAT

SELECT
    m.brand_name,
    m.strength,
    m.dosage_form,
    man.name         AS manufacturer,
    msm.composition_strength
FROM Medicines m
JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
JOIN Salts s                   ON msm.salt_id   = s.salt_id
JOIN Manufacturers man         ON m.manufacturer_id = man.manufacturer_id
WHERE LOWER(s.salt_name) LIKE '%paracetamol%'
  AND m.is_active = 1
ORDER BY m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q2. Find all medicines made by a specific manufacturer
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: JOIN, WHERE, ORDER BY

SELECT
    m.medicine_id,
    m.brand_name,
    m.strength,
    m.dosage_form,
    m.prescription_status,
    c.category_name
FROM Medicines m
JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
JOIN Categories c      ON m.category_id     = c.category_id
WHERE LOWER(man.name) LIKE '%cipla%'
  AND m.is_active = 1
ORDER BY c.category_name, m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q3. Partial OCR text search — multi-field LIKE matching
-- ─────────────────────────────────────────────────────────────
-- This is what the search engine does programmatically.
-- Demonstrates: multi-table OR, GROUP BY, CASE scoring

SELECT
    m.medicine_id,
    m.brand_name,
    m.strength,
    man.name AS manufacturer,
    GROUP_CONCAT(DISTINCT s.salt_name) AS salts,
    CASE
        WHEN UPPER(m.brand_name) LIKE UPPER('%TORR%') THEN 'brand_fragment (+15)'
        WHEN UPPER(man.name)     LIKE UPPER('%TORR%') THEN 'manufacturer (+12)'
        WHEN UPPER(s.salt_name)  LIKE UPPER('%TORR%') THEN 'salt_fragment (+20)'
        ELSE 'other'
    END AS match_field
FROM Medicines m
JOIN Manufacturers man         ON m.manufacturer_id = man.manufacturer_id
LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
LEFT JOIN Salts s              ON msm.salt_id = s.salt_id
WHERE (
    UPPER(m.brand_name)  LIKE UPPER('%TORR%')
 OR UPPER(man.name)      LIKE UPPER('%TORR%')
 OR UPPER(s.salt_name)   LIKE UPPER('%TORR%')
 OR UPPER(m.strength)    LIKE UPPER('%50%')
)
  AND m.is_active = 1
GROUP BY m.medicine_id
ORDER BY m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q4. Find same-composition medicines (relational chain join)
-- ─────────────────────────────────────────────────────────────
-- Medicine → Salt → Medicine (M:N traversal)
-- Demonstrates: self-join via junction table, relational power

SELECT DISTINCT
    target.brand_name       AS original_medicine,
    s.salt_name             AS shared_salt,
    alt.brand_name          AS alternative_medicine,
    alt.strength            AS alt_strength,
    alt_man.name            AS alt_manufacturer
FROM Medicines target
JOIN Medicine_Salt_Mapping msm1 ON target.medicine_id = msm1.medicine_id
JOIN Salts s                    ON msm1.salt_id = s.salt_id
JOIN Medicine_Salt_Mapping msm2 ON msm2.salt_id = msm1.salt_id
                                AND msm2.medicine_id != target.medicine_id
JOIN Medicines alt              ON msm2.medicine_id = alt.medicine_id
JOIN Manufacturers alt_man      ON alt.manufacturer_id = alt_man.manufacturer_id
WHERE LOWER(target.brand_name) LIKE '%augmentin%'
  AND alt.is_active = 1
ORDER BY s.salt_name, alt.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q5. Manufacturers with most medicines (aggregate/ranked)
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: GROUP BY, COUNT, ORDER BY, aggregate functions

SELECT
    man.name                      AS manufacturer,
    man.city,
    COUNT(m.medicine_id)          AS medicine_count,
    COUNT(DISTINCT m.category_id) AS categories_covered,
    GROUP_CONCAT(DISTINCT c.category_name) AS categories
FROM Manufacturers man
JOIN Medicines m ON man.manufacturer_id = m.manufacturer_id AND m.is_active = 1
JOIN Categories c ON m.category_id = c.category_id
GROUP BY man.manufacturer_id
ORDER BY medicine_count DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q6. Find medicines in a particular category
-- ─────────────────────────────────────────────────────────────
SELECT
    m.brand_name,
    m.strength,
    m.dosage_form,
    m.prescription_status,
    man.name AS manufacturer
FROM Medicines m
JOIN Categories c      ON m.category_id     = c.category_id
JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
WHERE LOWER(c.category_name) LIKE '%antihypertensive%'
  AND m.is_active = 1
ORDER BY m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q7. Multi-signal search using multiple OCR tokens
-- ─────────────────────────────────────────────────────────────
-- Simulates: tokens ["ZAM", "50", "TORR"]
-- Demonstrates: compound WHERE with multiple signals

SELECT
    m.medicine_id,
    m.brand_name,
    m.strength,
    man.name AS manufacturer,
    GROUP_CONCAT(DISTINCT s.salt_name) AS salts,
    pd.packaging_keywords
FROM Medicines m
JOIN Manufacturers man             ON m.manufacturer_id = man.manufacturer_id
LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
LEFT JOIN Salts s                  ON msm.salt_id = s.salt_id
LEFT JOIN Packaging_Details pd     ON m.medicine_id = pd.medicine_id
WHERE (
       UPPER(m.brand_name)           LIKE '%ZAM%'
    OR UPPER(man.name)               LIKE '%TORR%'
    OR UPPER(man.short_name)         LIKE '%TORR%'
    OR UPPER(m.strength)             LIKE '%50%'
    OR UPPER(pd.packaging_keywords)  LIKE '%ZAM%'
)
  AND m.is_active = 1
GROUP BY m.medicine_id
ORDER BY m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q8. Most searched medicines (aggregate on history)
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: JOIN on Search_History, GROUP BY, aggregate

SELECT
    m.brand_name,
    man.name         AS manufacturer,
    COUNT(sh.search_id) AS times_matched,
    AVG(sh.top_match_score) AS avg_confidence,
    MAX(sh.search_timestamp) AS last_searched
FROM Search_History sh
JOIN Medicines m    ON sh.top_match_id = m.medicine_id
JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
GROUP BY m.medicine_id
ORDER BY times_matched DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q9. Medicines with incomplete metadata
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: IS NULL checks, data quality query

SELECT
    m.medicine_id,
    m.brand_name,
    m.strength,
    man.name AS manufacturer,
    CASE WHEN m.dosage_form   IS NULL THEN '✗' ELSE '✓' END AS has_form,
    CASE WHEN m.uses          IS NULL THEN '✗' ELSE '✓' END AS has_uses,
    CASE WHEN m.warnings      IS NULL THEN '✗' ELSE '✓' END AS has_warnings,
    CASE WHEN m.storage_info  IS NULL THEN '✗' ELSE '✓' END AS has_storage,
    CASE WHEN pd.packaging_id IS NULL THEN '✗' ELSE '✓' END AS has_packaging
FROM Medicines m
JOIN Manufacturers man         ON m.manufacturer_id = man.manufacturer_id
LEFT JOIN Packaging_Details pd ON m.medicine_id = pd.medicine_id
WHERE (
    m.dosage_form  IS NULL
 OR m.uses         IS NULL
 OR m.warnings     IS NULL
)
  AND m.is_active = 1
ORDER BY m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q10. Medicines whose source has not been verified recently
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: NOT EXISTS subquery, date functions

SELECT
    m.medicine_id,
    m.brand_name,
    ms.source_name,
    ms.source_type,
    ms.date_collected,
    ms.verification_status
FROM Medicines m
JOIN Medicine_Sources ms ON m.medicine_id = ms.medicine_id
WHERE ms.verification_status != 'verified'
   OR ms.last_verified IS NULL
ORDER BY ms.date_collected ASC;


-- ─────────────────────────────────────────────────────────────
-- Q11. Which salts appear in the most medicines? (salt freq)
-- ─────────────────────────────────────────────────────────────
SELECT
    s.salt_name,
    s.drug_class,
    COUNT(msm.medicine_id) AS medicine_count
FROM Salts s
JOIN Medicine_Salt_Mapping msm ON s.salt_id = msm.salt_id
JOIN Medicines m ON msm.medicine_id = m.medicine_id AND m.is_active = 1
GROUP BY s.salt_id
ORDER BY medicine_count DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q12. Full medicine info via SQL VIEW (3NF joined view)
-- ─────────────────────────────────────────────────────────────
SELECT * FROM v_medicine_full WHERE brand_name LIKE '%Dolo%';


-- ─────────────────────────────────────────────────────────────
-- Q13. UNF flat view — normalization demo
-- ─────────────────────────────────────────────────────────────
SELECT * FROM v_unf_flat LIMIT 5;


-- ─────────────────────────────────────────────────────────────
-- Q14. Show prescription vs OTC distribution
-- ─────────────────────────────────────────────────────────────
SELECT
    prescription_status,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Medicines WHERE is_active=1), 1) AS percentage
FROM Medicines
WHERE is_active = 1
GROUP BY prescription_status;


-- ─────────────────────────────────────────────────────────────
-- Q15. TRANSACTION example — add a medicine with its salt mapping
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: ACID transaction

BEGIN TRANSACTION;

    INSERT INTO Medicines
        (brand_name, strength, dosage_form, prescription_status, manufacturer_id, category_id)
    VALUES
        ('Demo Medicine', '100mg', 'Tablet', 'OTC', 1, 1);

    INSERT INTO Medicine_Salt_Mapping (medicine_id, salt_id, composition_strength)
    VALUES (last_insert_rowid(), 1, '100mg');

COMMIT;

-- To undo:
-- ROLLBACK;


-- ─────────────────────────────────────────────────────────────
-- Q16. OCR keyword index lookup (fast keyword-based retrieval)
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: use of index idx_ocr_keywords_kw

SELECT
    ok.keyword,
    ok.keyword_type,
    m.brand_name,
    m.strength,
    man.name AS manufacturer
FROM OCR_Keywords ok
JOIN Medicines m        ON ok.medicine_id    = m.medicine_id
JOIN Manufacturers man  ON m.manufacturer_id = man.manufacturer_id
WHERE ok.keyword LIKE 'TOZA%'
  AND m.is_active = 1;


-- ─────────────────────────────────────────────────────────────
-- Q17. Pharmacy stock — medicines available and their prices
-- ─────────────────────────────────────────────────────────────
-- Demonstrates: M:N pharmacy-medicine join with attributes

SELECT
    p.name           AS pharmacy,
    p.city,
    m.brand_name,
    m.strength,
    ps.price,
    ps.quantity
FROM Pharmacy_Stock ps
JOIN Pharmacies  p ON ps.pharmacy_id = p.pharmacy_id
JOIN Medicines   m ON ps.medicine_id = m.medicine_id
WHERE m.is_active = 1
ORDER BY p.name, m.brand_name;


-- ─────────────────────────────────────────────────────────────
-- Q18. Manufacturer stats view
-- ─────────────────────────────────────────────────────────────
SELECT * FROM v_manufacturer_stats ORDER BY total_medicines DESC;
