# Review 2 — Talking Points (Tables, EER, Normalization)

## 1. The real-life problem, in one line
A patient/pharmacist is left with a **cut blister strip** — the printed brand name,
salt composition, manufacturer, batch, and expiry are partially or fully missing.
There is no structured way to reconstruct the medicine's full record from that
fragment. This system takes a partial text fragment (or, later, an OCR'd photo)
and returns ranked candidate medicines with their complete record.

## 2. Why the schema looks the way it does
Each table exists because a real fragment of the problem needs it:

| Table | Real-world reason it exists |
|---|---|
| `Medicines` | The core catalogue entry — brand, strength, visual identifiers (color/shape/strip size) a patient can still see even with no text |
| `Salts` + `Medicine_Salt_Mapping` | A brand can contain multiple salts, and a salt appears in many brands (Augmentin = Amoxicillin + Clavulanate) — a classic M:N, so it cannot live as a column on `Medicines` |
| `Manufacturers` | Printed manufacturer name is often the only surviving text on a cut strip — one manufacturer makes many medicines (1:M) |
| `Categories` | Groups medicines therapeutically (analgesic, antibiotic, ...) — 1:M |
| `Batches` | Expiry/mfg date is **batch-level**, not brand-level — a brand has many batches over time (1:M). This is *why* batch and brand are separate tables: fabricating one expiry per brand would be wrong |
| `Pharmacies` + `Pharmacy_Stock` | "Where can I still buy this" — M:N between medicines and pharmacies, with price/quantity as relationship attributes |
| `Users` + `Search_History` | Every search is logged per user (1:M) — supports the "search history" objective |

This is the EER → relational mapping story for slide 7/8.

## 3. Normalization argument (what to say when asked "why is this 3NF?")
- **1NF violation (UNF view in the app):** the flattened view group-concats a
  medicine's salts and batches into one repeating text field per row
  (`Salts_List`, `Batches_List`) — a multivalued attribute in a single cell.
- **Decomposition to 1NF:** repeating groups pulled into `Medicine_Salt_Mapping`
  and `Batches`, each with its own row per fact.
- **2NF:** every non-key attribute depends on the *whole* primary key — relevant
  on the composite-key table `Medicine_Salt_Mapping` (`medicine_id, salt_id`):
  `composition_strength` depends on the pair, not on either column alone.
- **3NF:** no transitive dependencies — e.g. `Manufacturer_Address` is **not**
  stored on `Medicines`; it lives only in `Manufacturers`, reachable via
  `manufacturer_id`. Same for `Category_Name` via `category_id`. This is the
  concrete fix the UNF→Normalized toggle demonstrates in the app.

The app's **"View UNF" vs "Click to Normalize"** toggle on the Medicines table
*is* this argument, live — that's the section to demo first.

## 4. What changed for this review pass
- **Enter-key search:** the search box now triggers `performSearch()` on
  `Enter`, not just the button click (`frontend/app.js`, `window.onload`).
- **OCR stays a simulation on purpose.** `simulateOCR()` picks a random mock
  fragment instead of running real OCR — Tesseract integration is listed as
  the "Optional OCR" component on the hardware/software slide, scoped for a
  later phase, not Review 2. Don't present it as broken; present it as a
  deliberately stubbed step so the demo stays deterministic.

## 5. Suggested demo order for the review
1. Search box → type a fragment (`olo`, `aug`, `cet`) → press **Enter** → ranked results.
2. Normalization section → show **UNF** (repeating salts/batches in one row) → click **Normalize** → same data, decomposed.
3. EER Explorer → click through 2-3 tables (`Medicines`, `Medicine_Salt_Mapping`, `Batches`) to show FK relationships live against `schema.sql`.
4. Tie back to slide 7 (relational model) and slide 8 (ER diagram) as the design source for what's now running.
