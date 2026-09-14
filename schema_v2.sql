-- ============================================================
-- Medicine Information Retrieval System — Schema v2
-- FastAPI + SQLite backend | 3NF normalized | DBMS DA-3
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- CORE LOOKUP / DIMENSION TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS Manufacturers (
    manufacturer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name              VARCHAR(150) NOT NULL UNIQUE,
    short_name        VARCHAR(50),           -- e.g. "Torrent" for "Torrent Pharmaceuticals"
    address           VARCHAR(255),
    city              VARCHAR(100),
    state             VARCHAR(100),
    country           VARCHAR(50) DEFAULT 'India',
    website           VARCHAR(255),
    logo_url          TEXT
);

CREATE TABLE IF NOT EXISTS Categories (
    category_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name  VARCHAR(100) NOT NULL UNIQUE,
    description    TEXT
);

CREATE TABLE IF NOT EXISTS Salts (
    salt_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    salt_name    VARCHAR(200) NOT NULL UNIQUE,
    iupac_name   TEXT,
    drug_class   VARCHAR(100)
);

-- ============================================================
-- CORE MEDICINE TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS Medicines (
    medicine_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name          VARCHAR(150) NOT NULL,
    generic_name        VARCHAR(200),
    strength            VARCHAR(50)  NOT NULL,
    dosage_form         VARCHAR(50),          -- Tablet, Capsule, Syrup, Injection, etc.
    prescription_status VARCHAR(20)  DEFAULT 'OTC' CHECK(prescription_status IN ('OTC','Rx','Schedule H','Schedule H1','Schedule X')),
    tablet_color        VARCHAR(50),
    tablet_shape        VARCHAR(50),
    strip_size          VARCHAR(50),          -- e.g. "10 Tablets", "15 Capsules"
    uses                TEXT,                 -- General therapeutic use (not personal advice)
    warnings            TEXT,
    storage_info        TEXT,
    manufacturer_id     INTEGER NOT NULL,
    category_id         INTEGER NOT NULL,
    is_active           INTEGER DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturers(manufacturer_id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id)     REFERENCES Categories(category_id)        ON DELETE RESTRICT,
    UNIQUE (brand_name, strength, manufacturer_id)
);

-- ============================================================
-- MANY-TO-MANY: Medicines <-> Salts
-- ============================================================

CREATE TABLE IF NOT EXISTS Medicine_Salt_Mapping (
    medicine_id          INTEGER NOT NULL,
    salt_id              INTEGER NOT NULL,
    composition_strength VARCHAR(50),
    PRIMARY KEY (medicine_id, salt_id),
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE,
    FOREIGN KEY (salt_id)     REFERENCES Salts(salt_id)         ON DELETE CASCADE
);

-- ============================================================
-- BATCH-LEVEL DATA (batch != medicine; expiry is per batch)
-- ============================================================

CREATE TABLE IF NOT EXISTS Batches (
    batch_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    batch_no    VARCHAR(50) NOT NULL UNIQUE,
    mfg_date    DATE NOT NULL,
    exp_date    DATE NOT NULL,
    CHECK (exp_date > mfg_date),
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE
);

-- ============================================================
-- PACKAGING METADATA (visual identification aid)
-- ============================================================

CREATE TABLE IF NOT EXISTS Packaging_Details (
    packaging_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id        INTEGER NOT NULL UNIQUE,
    dominant_color     VARCHAR(50),       -- dominant strip/box color
    secondary_color    VARCHAR(50),
    strip_count        INTEGER,           -- tablets per strip
    packaging_type     VARCHAR(50),       -- Blister strip, Bottle, Vial, etc.
    packaging_keywords TEXT,             -- comma-sep visible text on packaging
    logo_description   TEXT,
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE
);

-- ============================================================
-- OCR KEYWORD HINTS (pre-indexed search fragments per medicine)
-- ============================================================

CREATE TABLE IF NOT EXISTS OCR_Keywords (
    keyword_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id  INTEGER NOT NULL,
    keyword      VARCHAR(100) NOT NULL,
    keyword_type VARCHAR(40) CHECK(keyword_type IN (
                     'brand_fragment','salt_fragment',
                     'manufacturer_fragment','packaging','strength_fragment')),
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE
);

-- ============================================================
-- DATA PROVENANCE / SOURCES
-- ============================================================

CREATE TABLE IF NOT EXISTS Medicine_Sources (
    source_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id         INTEGER NOT NULL,
    source_name         VARCHAR(150) NOT NULL,
    source_url          TEXT,
    source_type         VARCHAR(50) CHECK(source_type IN (
                            'manufacturer_page','govt_dataset',
                            'regulatory','package_insert','manual')),
    date_collected      DATE,
    last_verified       DATE,
    verification_status VARCHAR(30) DEFAULT 'unverified'
                            CHECK(verification_status IN ('verified','unverified','disputed')),
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE
);

-- ============================================================
-- PHARMACIES & STOCK (M:N with attributes)
-- ============================================================

CREATE TABLE IF NOT EXISTS Pharmacies (
    pharmacy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(150) NOT NULL,
    address     VARCHAR(255),
    city        VARCHAR(100),
    latitude    REAL,
    longitude   REAL,
    contact     VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS Pharmacy_Stock (
    stock_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacy_id INTEGER NOT NULL,
    medicine_id INTEGER NOT NULL,
    price       REAL    NOT NULL CHECK(price >= 0),
    quantity    INTEGER NOT NULL CHECK(quantity >= 0),
    UNIQUE(pharmacy_id, medicine_id),
    FOREIGN KEY (pharmacy_id) REFERENCES Pharmacies(pharmacy_id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id)  ON DELETE CASCADE
);

-- ============================================================
-- USERS (supports Google OAuth + email/pass)
-- ============================================================

CREATE TABLE IF NOT EXISTS Users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name           VARCHAR(100) NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    google_id      VARCHAR(100) UNIQUE,      -- Google sub ID for OAuth
    avatar_url     TEXT,
    role           VARCHAR(20) DEFAULT 'user' CHECK(role IN ('user','admin')),
    password_hash  TEXT,                     -- NULL for OAuth-only users
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login     DATETIME
);

-- ============================================================
-- SEARCH HISTORY (per user or anonymous)
-- ============================================================

CREATE TABLE IF NOT EXISTS Search_History (
    search_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER,
    query_text          VARCHAR(500) NOT NULL,
    search_mode         VARCHAR(20) DEFAULT 'text' CHECK(search_mode IN ('text','ocr','combined')),
    top_match_id        INTEGER,
    top_match_score     REAL,
    result_count        INTEGER DEFAULT 0,
    search_timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)       REFERENCES Users(user_id)       ON DELETE SET NULL,
    FOREIGN KEY (top_match_id)  REFERENCES Medicines(medicine_id) ON DELETE SET NULL
);

-- ============================================================
-- INDEXES (for fast partial-text search)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_medicines_brand       ON Medicines(brand_name);
CREATE INDEX IF NOT EXISTS idx_medicines_strength    ON Medicines(strength);
CREATE INDEX IF NOT EXISTS idx_medicines_manufacturer ON Medicines(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_medicines_category    ON Medicines(category_id);
CREATE INDEX IF NOT EXISTS idx_medicines_active      ON Medicines(is_active);
CREATE INDEX IF NOT EXISTS idx_salts_name            ON Salts(salt_name);
CREATE INDEX IF NOT EXISTS idx_manufacturers_name    ON Manufacturers(name);
CREATE INDEX IF NOT EXISTS idx_manufacturers_short   ON Manufacturers(short_name);
CREATE INDEX IF NOT EXISTS idx_ocr_keywords_kw       ON OCR_Keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_ocr_keywords_med      ON OCR_Keywords(medicine_id);
CREATE INDEX IF NOT EXISTS idx_msm_medicine          ON Medicine_Salt_Mapping(medicine_id);
CREATE INDEX IF NOT EXISTS idx_msm_salt              ON Medicine_Salt_Mapping(salt_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user   ON Search_History(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_ts     ON Search_History(search_timestamp);
CREATE INDEX IF NOT EXISTS idx_batches_medicine      ON Batches(medicine_id);

-- ============================================================
-- SQL VIEWS (for DBMS demonstration)
-- ============================================================

-- Full medicine info view (used by /api/medicine/{id})
CREATE VIEW IF NOT EXISTS v_medicine_full AS
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
    m.is_active,
    man.name          AS manufacturer_name,
    man.short_name    AS manufacturer_short,
    man.city          AS manufacturer_city,
    man.state         AS manufacturer_state,
    man.website       AS manufacturer_website,
    c.category_name,
    GROUP_CONCAT(s.salt_name || ' (' || msm.composition_strength || ')', ', ') AS salts_composition,
    pd.dominant_color,
    pd.strip_count,
    pd.packaging_keywords
FROM Medicines m
JOIN  Manufacturers man      ON m.manufacturer_id = man.manufacturer_id
JOIN  Categories c           ON m.category_id     = c.category_id
LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
LEFT JOIN Salts s            ON msm.salt_id = s.salt_id
LEFT JOIN Packaging_Details pd ON m.medicine_id = pd.medicine_id
GROUP BY m.medicine_id;

-- UNF flat view (1NF violation demonstration)
CREATE VIEW IF NOT EXISTS v_unf_flat AS
SELECT
    m.brand_name          AS Brand_Name,
    m.strength            AS Strength,
    m.prescription_status AS Prescription_Status,
    m.tablet_color        AS Tablet_Color,
    m.tablet_shape        AS Tablet_Shape,
    m.strip_size          AS Strip_Size,
    GROUP_CONCAT(s.salt_name || ': ' || msm.composition_strength, ' | ') AS Salts_List,
    man.name              AS Manufacturer_Name,
    man.address || ', ' || man.city || ', ' || man.state AS Manufacturer_Address,
    c.category_name       AS Category_Name,
    GROUP_CONCAT(b.batch_no || ' (Exp: ' || b.exp_date || ')', ' | ') AS Batches_List
FROM Medicines m
JOIN  Manufacturers man      ON m.manufacturer_id = man.manufacturer_id
JOIN  Categories c           ON m.category_id     = c.category_id
LEFT JOIN Medicine_Salt_Mapping msm ON m.medicine_id = msm.medicine_id
LEFT JOIN Salts s            ON msm.salt_id = s.salt_id
LEFT JOIN Batches b          ON m.medicine_id = b.medicine_id
WHERE m.is_active = 1
GROUP BY m.medicine_id;

-- Search statistics view
CREATE VIEW IF NOT EXISTS v_search_stats AS
SELECT
    m.brand_name,
    man.name AS manufacturer,
    COUNT(sh.search_id) AS search_count,
    MAX(sh.search_timestamp) AS last_searched
FROM Search_History sh
JOIN Medicines m    ON sh.top_match_id = m.medicine_id
JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
GROUP BY m.medicine_id
ORDER BY search_count DESC;

-- Same-composition medicines view
CREATE VIEW IF NOT EXISTS v_same_composition AS
SELECT
    s.salt_name,
    m.medicine_id,
    m.brand_name,
    m.strength,
    m.dosage_form,
    man.name AS manufacturer
FROM Medicine_Salt_Mapping msm
JOIN Salts s         ON msm.salt_id = s.salt_id
JOIN Medicines m     ON msm.medicine_id = m.medicine_id
JOIN Manufacturers man ON m.manufacturer_id = man.manufacturer_id
WHERE m.is_active = 1;

-- Manufacturer medicine count view
CREATE VIEW IF NOT EXISTS v_manufacturer_stats AS
SELECT
    man.name              AS manufacturer,
    man.city,
    COUNT(m.medicine_id)  AS total_medicines,
    COUNT(DISTINCT m.category_id) AS categories_covered
FROM Manufacturers man
LEFT JOIN Medicines m ON man.manufacturer_id = m.manufacturer_id AND m.is_active = 1
GROUP BY man.manufacturer_id;

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Auto-generate OCR keyword hints when a medicine is inserted
CREATE TRIGGER IF NOT EXISTS trg_auto_ocr_keywords
AFTER INSERT ON Medicines
BEGIN
    -- Insert brand name fragments (first 4 chars, last 3 chars, full name)
    INSERT OR IGNORE INTO OCR_Keywords(medicine_id, keyword, keyword_type)
    VALUES
        (NEW.medicine_id, UPPER(SUBSTR(NEW.brand_name, 1, 4)), 'brand_fragment'),
        (NEW.medicine_id, UPPER(SUBSTR(NEW.brand_name, -3)),   'brand_fragment'),
        (NEW.medicine_id, UPPER(NEW.strength),                  'strength_fragment');
END;

-- Log search_timestamp update
CREATE TRIGGER IF NOT EXISTS trg_update_last_login
AFTER UPDATE OF last_login ON Users
BEGIN
    SELECT DATETIME('now');
END;
