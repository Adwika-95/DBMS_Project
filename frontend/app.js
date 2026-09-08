const API_BASE = "http://127.0.0.1:8000/api";

window.onload = function() {
    loadUNF();
    loadTable('Medicines');

    // Allow search to be triggered by pressing Enter, not just the Search button
    const searchInput = document.getElementById("searchInput");
    searchInput.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            performSearch();
        }
    });
};
// Add this new function to simulate the camera OCR step
function simulateOCR() {
    const mockFragments = ["olo 65", "ugment", "tzine", "telm"];
    const randomFragment = mockFragments[Math.floor(Math.random() * mockFragments.length)];
    const input = document.getElementById("searchInput");
    input.value = randomFragment;
    
    const box = document.getElementById("searchResults");
    box.style.display = "block";
    box.innerHTML = `<span style="color:#00796b;">📷 OCR extracted text: <strong>"${randomFragment}"</strong></span>. Fetching matches...`;
    
    setTimeout(performSearch, 800);
}

// Replace your existing performSearch function with this updated one
async function performSearch() {
    const q = document.getElementById("searchInput").value.trim();
    const box = document.getElementById("searchResults");
    if (!q) return;

    box.style.display = "block";
    if (!box.innerHTML.includes("OCR")) {
        box.innerHTML = "Searching database...";
    }

    try {
        const res = await fetch(`${API_BASE}/search?query=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (!data.results || data.results.length === 0) {
            box.innerHTML = `No matches found for fragment '<strong>${q}</strong>'.`;
            return;
        }
        
        let html = `<div style="margin-bottom: 10px;"><strong>Recovered ${data.results.length} Match(es) for "${q}":</strong></div>`;
        
        data.results.forEach(r => {
            html += `
            <div style="border-left: 4px solid #26a69a; padding-left: 10px; margin-bottom: 15px; background: white; padding: 10px; border-radius: 4px; border: 1px solid #d1d5db;">
                <div style="display:flex; justify-content: space-between;">
                    <strong style="color: #004d40; font-size: 1.1rem;">${r.brand_name} (${r.strength})</strong>
                    <span style="font-size: 0.8rem; background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">Rank ${r.match_rank}: ${r.match_type}</span>
                </div>
                <div style="font-size: 0.85rem; margin-top: 5px; color: #334155;">
                    <div><strong>Salt:</strong> ${r.salts_composition || 'N/A'}</div>
                    <div><strong>Mfg:</strong> ${r.manufacturer_name} | <strong>Category:</strong> ${r.category_name}</div>
                    <div><strong>Visual:</strong> ${r.tablet_color}, ${r.tablet_shape} | <strong>Strip:</strong> ${r.strip_size}</div>
                </div>
            </div>`;
        });
        
        box.innerHTML = html;
    } catch (e) {
        box.innerHTML = "Error connecting to backend API.";
    }
}
async function switchView(mode) {
    const btnUNF = document.getElementById("btnUNF");
    const btnNorm = document.getElementById("btnNorm");
    const desc = document.getElementById("viewDescription");

    if (mode === 'unf') {
        btnUNF.classList.add("active-tab");
        btnNorm.classList.remove("active-tab");
        desc.textContent = "Showing initial flat table with repeating salt and batch groups (Violation of 1NF).";
        loadUNF();
    } else {
        btnNorm.classList.add("active-tab");
        btnUNF.classList.remove("active-tab");
        desc.textContent = "Normalized 3NF / EER relational tables decomposed into independent entities with foreign keys.";
        loadNormalizedTablesOverview();
    }
}

async function loadUNF() {
    const container = document.getElementById("tableContainer");
    container.innerHTML = "Loading UNF table...";
    try {
        const res = await fetch(`${API_BASE}/unf`);
        const data = await res.json();
        renderTable(container, data.columns, data.rows);
    } catch (e) {
        container.innerHTML = "Failed to load UNF data. Ensure backend is running.";
    }
}

async function loadNormalizedTablesOverview() {
    const container = document.getElementById("tableContainer");
    container.innerHTML = "Loading Normalized Tables (Medicines & Manufacturers joined)...";
    try {
        const res = await fetch(`${API_BASE}/tables/Medicines`);
        const data = await res.json();
        renderTable(container, data.columns, data.rows);
    } catch (e) {
        container.innerHTML = "Failed to load normalized data.";
    }
}

async function loadTable(tableName) {
    document.getElementById("currentTableName").textContent = `Table: ${tableName}`;
    const container = document.getElementById("schemaTableContainer");
    container.innerHTML = `Loading ${tableName}...`;
    try {
        const res = await fetch(`${API_BASE}/tables/${tableName}`);
        const data = await res.json();
        renderTable(container, data.columns, data.rows);
    } catch (e) {
        container.innerHTML = "Failed to load table data.";
    }
}

function renderTable(container, columns, rows) {
    if (!rows || rows.length === 0) {
        container.innerHTML = "<p style='padding:15px;'>No records found in this table.</p>";
        return;
    }
    let html = "<table><thead><tr>";
    columns.forEach(col => html += `<th>${col}</th>`);
    html += "</tr></thead><tbody>";
    rows.forEach(row => {
        html += "<tr>";
        columns.forEach(col => html += `<td>${row[col] !== null ? row[col] : ''}</td>`);
        html += "</tr>";
    });
    html += "</tbody></table>";
    container.innerHTML = html;
}