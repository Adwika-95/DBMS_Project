-- EER Diagram Relational Schema (3NF / BCNF Normalized)
CREATE TABLE IF NOT EXISTS Manufacturers (
    manufacturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Salts (
    salt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    salt_name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Medicines (
    medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name VARCHAR(150) NOT NULL,
    strength VARCHAR(50) NOT NULL,
    prescription_status VARCHAR(20) DEFAULT 'OTC',
    tablet_color VARCHAR(50),
    tablet_shape VARCHAR(50),
    strip_size VARCHAR(50),
    manufacturer_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturers(manufacturer_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Medicine_Salt_Mapping (
    medicine_id INTEGER NOT NULL,
    salt_id INTEGER NOT NULL,
    composition_strength VARCHAR(50),
    PRIMARY KEY (medicine_id, salt_id),
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE,
    FOREIGN KEY (salt_id) REFERENCES Salts(salt_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    batch_no VARCHAR(50) NOT NULL UNIQUE,
    mfg_date DATE NOT NULL,
    exp_date DATE NOT NULL,
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Pharmacies (
    pharmacy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    contact VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS Pharmacy_Stock (
    stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pharmacy_id INTEGER NOT NULL,
    medicine_id INTEGER NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (pharmacy_id) REFERENCES Pharmacies(pharmacy_id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Search_History (
    search_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query_text VARCHAR(255) NOT NULL,
    matched_medicine_id INTEGER,
    search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (matched_medicine_id) REFERENCES Medicines(medicine_id) ON DELETE SET NULL
);