# Medicine Information Retrieval System

A DBMS project (Richika, Adwika) that reconstructs full medicine information —
brand, salts, manufacturer, batch, expiry — from a partial text fragment (e.g.
what's still readable on a cut blister strip). Backend: FastAPI + SQLite.
Frontend: plain HTML/CSS/JS.

## Project structure

```
Medicine_Retrieval/
├── backend/
│   ├── app.py           # FastAPI routes (search, table explorer, UNF view)
│   └── database.py      # SQLite connection helper
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── schema.sql            # Table definitions (3NF / EER schema)
├── seed_data.py           # Creates + populates medicine_system.db from schema.sql
├── requirements.txt
└── medicine_system.db     # SQLite DB (created by seed_data.py — safe to delete and re-run)
```

## Prerequisites

- Python 3.10+
- A code editor (VS Code recommended) with a terminal

## Setup

**1. Get the code**

Clone the repo (or unzip the project folder) and open it in VS Code:
```
git clone <repo-url>
cd Medicine_Retrieval
```

**2. Create and activate a virtual environment**

Windows (cmd):
```
python -m venv venv
venv\Scripts\activate
```

Windows (PowerShell):
```
python -m venv venv
venv\Scripts\Activate.ps1
```
If PowerShell blocks the script, run this once first:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

Mac/Linux:
```
python3 -m venv venv
source venv/bin/activate
```

You'll know it worked when your prompt shows a `(venv)` prefix.

**3. Install dependencies**
```
pip install -r requirements.txt
```

**4. Seed the database**

This builds `medicine_system.db` from `schema.sql` and loads sample data
(manufacturers, medicines, salts, batches, pharmacies).
```
python seed_data.py
```
You should see: `Database seeded successfully.`
Safe to re-run any time — delete `medicine_system.db` first if you want a clean rebuild.

## Running the app

**Terminal 1 — backend** (run from the `Medicine_Retrieval` root, not from inside `backend/`):
```
uvicorn backend.app:app --reload --port 8000
```
If `uvicorn` isn't recognized, use:
```
python -m uvicorn backend.app:app --reload --port 8000
```
Check it's up: open `http://127.0.0.1:8000/api/search?query=olo` in a browser —
you should get a JSON response.

**Terminal 2 — frontend** (open a second terminal, keep the backend running):
```
cd frontend
python -m http.server 5500
```
Then open `http://127.0.0.1:5500` in your browser.

*(Alternative: if you have the VS Code "Live Server" extension, right-click
`frontend/index.html` → "Open with Live Server" instead of the `http.server` step.)*

## Using it

- **Search:** type a fragment (`olo`, `aug`, `cet`, `pan`, `telm`) and press
  **Enter** or click Search — returns ranked matches by brand/salt/manufacturer.
- **Normalization demo:** the "View UNF" / "Click to Normalize" toggle shows
  the same data first as a flattened, repeating-group table (1NF violation),
  then decomposed into the actual 3NF tables.
- **EER Explorer:** browse any individual table (Medicines, Salts, Batches, etc.)
  to see the schema live against `schema.sql`.
- **OCR button:** currently a simulation only — it fills the search box with a
  random mock fragment instead of running real OCR. This is intentional for now.

## Common issues

| Problem | Fix |
|---|---|
| `'venv' is not recognized` | You're likely using the wrong activation command for your shell — see step 2 above (cmd vs PowerShell) |
| `'uvicorn' is not recognized` | venv isn't activated, or use `python -m uvicorn ...` instead |
| Frontend loads but search/tables show "Failed to load" | Backend isn't running, or you're not on port 8000 — check Terminal 1 |
| `no such table` errors | Run `python seed_data.py` again from the project root |
