/**
 * MedStrip — Clinical Decision Support & Medicine Retrieval
 * Frontend Client Application Logic
 */

const API_BASE = "http://127.0.0.1:8000/api";
let currentUser = null;
let uploadedFile = null;
let activeSearchTokens = [];

// ── Initialization ────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    checkCurrentUser();
    setupDragDrop();
    loadNormalizationData();

    // Enter key triggers search in input
    const input = document.getElementById("searchInput");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") performSearch();
        });
    }
});

// ── Tab Management ────────────────────────────────────────────────────────────

function switchSearchTab(mode) {
    const paneText = document.getElementById("paneTextSearch");
    const paneOcr = document.getElementById("paneOcrScan");
    const btnText = document.getElementById("tabModeText");
    const btnOcr = document.getElementById("tabModeOcr");

    if (mode === "text") {
        paneText.style.display = "block";
        paneOcr.style.display = "none";
        btnText.classList.add("active");
        btnOcr.classList.remove("active");
    } else {
        paneText.style.display = "none";
        paneOcr.style.display = "block";
        btnText.classList.remove("active");
        btnOcr.classList.add("active");
    }
}

function switchDbmsTab(tab) {
    const panes = {
        normalization: document.getElementById("paneNormalization"),
        tables: document.getElementById("paneTables"),
        views: document.getElementById("paneViews")
    };
    const btns = {
        normalization: document.getElementById("tabNorm"),
        tables: document.getElementById("tabTables"),
        views: document.getElementById("tabViews")
    };

    Object.keys(panes).forEach(k => {
        if (panes[k]) panes[k].style.display = (k === tab) ? "block" : "none";
        if (btns[k]) btns[k].classList.toggle("active", k === tab);
    });

    if (tab === "tables" && !document.getElementById("schemaTableContainer").querySelector("table")) {
        loadTable("Medicines");
    } else if (tab === "views" && !document.getElementById("viewsTableContainer").querySelector("table")) {
        loadView("v_medicine_full");
    }
}

function setQuery(text) {
    switchSearchTab("text");
    const input = document.getElementById("searchInput");
    input.value = text;
    performSearch();
}

function clearSearch() {
    const input = document.getElementById("searchInput");
    input.value = "";
    input.focus();
    const box = document.getElementById("searchResults");
    box.style.display = "none";
    box.innerHTML = "";
}

// ── Authentication ────────────────────────────────────────────────────────────

function getAuthHeaders() {
    const token = localStorage.getItem("medstrip_token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function checkCurrentUser() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, { headers: getAuthHeaders() });
        const data = await res.json();
        if (data.authenticated) {
            currentUser = data.user;
            document.getElementById("loginBtn").style.display = "none";
            const badge = document.getElementById("userBadge");
            badge.style.display = "flex";
            document.getElementById("userName").textContent = currentUser.name || currentUser.email;
            if (currentUser.picture) {
                document.getElementById("userAvatar").src = currentUser.picture;
            }
            if (currentUser.role === "admin") {
                document.getElementById("adminLink").style.display = "inline-block";
            }
        }
    } catch (e) {
        // Backend not ready or offline
    }
}

function loginGoogle() {
    window.location.href = `${API_BASE}/auth/google`;
}

function logout() {
    localStorage.removeItem("medstrip_token");
    currentUser = null;
    document.getElementById("loginBtn").style.display = "flex";
    document.getElementById("userBadge").style.display = "none";
    document.getElementById("adminLink").style.display = "none";
    showToast("Signed out successfully");
}

function showToast(msg, duration = 3000) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), duration);
}

// ── Blister Strip Scanner / Image Upload ──────────────────────────────────────

function setupDragDrop() {
    const zone = document.getElementById("uploadZone");
    if (!zone) return;

    zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("drag-over");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
    zone.addEventListener("drop", (e) => {
        e.preventDefault();
        zone.classList.remove("drag-over");
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith("image/")) {
            processImageFile(file);
        } else {
            showToast("Please provide a valid image file (JPEG, PNG, WebP)");
        }
    });
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) processImageFile(file);
}

function processImageFile(file) {
    uploadedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById("previewImg").src = e.target.result;
        document.getElementById("dropzoneIdle").style.display = "none";
        document.getElementById("uploadPreview").style.display = "flex";
        document.getElementById("uploadFileInfo").textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        document.getElementById("analysisStatusText").textContent = "Photo loaded • Click Analyze to process";

        // Reset previous analysis
        document.getElementById("structuredSignalsBox").style.display = "none";
        document.getElementById("tokenEditorArea").style.display = "none";

        // Automatically start analysis for instant experience
        performOCRSearch();
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    uploadedFile = null;
    document.getElementById("previewImg").src = "";
    document.getElementById("uploadPreview").style.display = "none";
    document.getElementById("dropzoneIdle").style.display = "flex";
    document.getElementById("imageFileInput").value = "";
    document.getElementById("structuredSignalsBox").style.display = "none";
    document.getElementById("tokenEditorArea").style.display = "none";
    document.getElementById("searchResults").style.display = "none";
}

// ── Search Handlers ───────────────────────────────────────────────────────────

async function performSearch() {
    const q = document.getElementById("searchInput").value.trim();
    if (!q) {
        showToast("Please enter a medicine name, salt, or strength");
        return;
    }

    const btn = document.getElementById("searchBtn");
    btn.disabled = true;
    btn.textContent = "Searching…";

    const box = document.getElementById("searchResults");
    box.style.display = "block";
    box.innerHTML = `<div class="table-loading-notice">Searching pharmaceutical database for "${q}"…</div>`;

    try {
        const res = await fetch(`${API_BASE}/search?query=${encodeURIComponent(q)}`, {
            headers: getAuthHeaders()
        });
        const data = await res.json();
        renderSearchResults(data, q);
    } catch (e) {
        box.innerHTML = `
            <div class="clinical-empty-box">
                <div class="empty-icon">!</div>
                <h3>Backend Server Unreachable</h3>
                <p>Ensure the FastAPI service is running on <code>http://127.0.0.1:8000</code>.</p>
            </div>
        `;
    }

    btn.disabled = false;
    btn.textContent = "Search Catalog";
}

async function performOCRSearch() {
    if (!uploadedFile) {
        showToast("Please select a blister strip image first");
        return;
    }

    const statusDiv = document.getElementById("ocrStatus");
    const statusTxt = document.getElementById("ocrStatusText");
    const box = document.getElementById("searchResults");
    const btn = document.getElementById("ocrScanBtn");

    btn.disabled = true;
    btn.textContent = "Extracting text…";
    statusDiv.style.display = "flex";
    statusTxt.textContent = "Preprocessing image & running EasyOCR neural network…";
    box.style.display = "block";
    box.innerHTML = `<div class="table-loading-notice">Analyzing blister strip foil print and matching chemical database…</div>`;

    const formData = new FormData();
    formData.append("file", uploadedFile);

    try {
        const res = await fetch(`${API_BASE}/ocr`, {
            method: "POST",
            body: formData,
            headers: getAuthHeaders()
        });
        const data = await res.json();
        statusDiv.style.display = "none";

        if (data.detail) {
            box.innerHTML = `
                <div class="clinical-empty-box">
                    <div class="empty-icon">!</div>
                    <h3>Analysis Error</h3>
                    <p>${data.detail}</p>
                </div>
            `;
            btn.disabled = false;
            btn.textContent = "Analyze & Match Medicine";
            return;
        }

        // Render structured signals
        if (data.structured_signals) {
            const sig = data.structured_signals;
            document.getElementById("structuredSignalsBox").style.display = "flex";
            document.getElementById("sigSalts").textContent = (sig.salts && sig.salts.length > 0)
                ? sig.salts.join(", ")
                : "Not clearly detected";
            document.getElementById("sigStrengths").textContent = (sig.strengths && sig.strengths.length > 0)
                ? sig.strengths.map(s => `${s} mg`).join(", ")
                : "Not clearly detected";
            document.getElementById("sigBrands").textContent = (sig.brands && sig.brands.length > 0)
                ? sig.brands.slice(0, 4).join(", ")
                : "Not clearly detected";

            document.getElementById("analysisStatusText").textContent = `Analysis complete • ${sig.detections_count || 0} text elements found`;
        }

        // Render editable token chips
        if (data.all_tokens && data.all_tokens.length > 0) {
            activeSearchTokens = [...data.all_tokens];
            renderTokenEditor(data.all_tokens);
        }

        // Render results
        renderSearchResults(data, (data.all_tokens || []).join(" "));

    } catch (e) {
        statusDiv.style.display = "none";
        box.innerHTML = `
            <div class="clinical-empty-box">
                <div class="empty-icon">!</div>
                <h3>OCR Extraction Failed</h3>
                <p>${e.message}</p>
            </div>
        `;
    }

    btn.disabled = false;
    btn.textContent = "Re-analyze Photo";
}

function renderTokenEditor(tokens) {
    const area = document.getElementById("tokenEditorArea");
    const list = document.getElementById("pillsList");
    if (!tokens || tokens.length === 0) {
        area.style.display = "none";
        return;
    }

    area.style.display = "flex";
    list.innerHTML = tokens.map(tok => `
        <span class="token-chip active-token" onclick="toggleToken(this, '${tok}')">
            ${tok}
            <span class="remove-token">✕</span>
        </span>
    `).join("");
}

function toggleToken(el, token) {
    el.classList.toggle("active-token");
    if (el.classList.contains("active-token")) {
        if (!activeSearchTokens.includes(token)) activeSearchTokens.push(token);
    } else {
        activeSearchTokens = activeSearchTokens.filter(t => t !== token);
    }

    // Re-run search with remaining active tokens
    if (activeSearchTokens.length > 0) {
        reSearchWithActiveTokens();
    }
}

async function reSearchWithActiveTokens() {
    const box = document.getElementById("searchResults");
    box.innerHTML = `<div class="table-loading-notice">Refining results with selected tokens…</div>`;

    try {
        const q = activeSearchTokens.join(" ");
        const res = await fetch(`${API_BASE}/search?query=${encodeURIComponent(q)}`, {
            headers: getAuthHeaders()
        });
        const data = await res.json();
        renderSearchResults(data, q);
    } catch (e) {
        // Handle error
    }
}

// ── Search Results Rendering ──────────────────────────────────────────────────

function renderSearchResults(data, query) {
    const box = document.getElementById("searchResults");
    const results = data.results || [];

    if (results.length === 0) {
        box.innerHTML = `
            <div class="clinical-empty-box">
                <div class="empty-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                </div>
                <h3>No Matching Medicine Found</h3>
                <p>No formulation in the database matched the extracted tokens "${query}". Try providing a clearer photo or manually entering visible brand or manufacturer fragments.</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="results-summary-bar">
            <span>Identified <strong>${results.length} formulation${results.length !== 1 ? "s" : ""}</strong> matching search clues</span>
            <span style="font-size: 0.76rem; color: var(--slate-500);">Ranked by chemical composition & dosage similarity</span>
        </div>
    `;

    results.forEach((r, idx) => {
        const confClass = r.confidence_pct >= 70 ? "high"
                        : r.confidence_pct >= 40 ? "medium"
                        : "low";

        const isScheduleH = (r.prescription_status === "Schedule H" || r.prescription_status === "Schedule H1");

        // Clue chips
        const clues = (r.matched_clues || []).slice(0, 5).map(c => `
            <span class="clue-chip">✓ ${c.label}</span>
        `).join("");

        html += `
            <article class="monograph-card">
                <div class="monograph-top-row">
                    <div>
                        <div class="med-brand-title">
                            ${r.brand_name}
                            <span class="strength-badge">${r.strength}</span>
                            <span class="form-badge">${r.dosage_form || "Tablet"}</span>
                            ${idx === 0 ? '<span class="form-badge" style="background:#f0fdf4;color:#15803d;border-color:#bbf7d0;">Primary Match</span>' : ''}
                        </div>
                        <div style="font-size:0.78rem; color:var(--slate-500); margin-top:2px;">
                            ${r.manufacturer_name || "Licensed Pharmaceutical Manufacturer"}
                        </div>
                    </div>

                    <div class="confidence-indicator-box">
                        <span class="conf-pill ${confClass}">
                            ${r.confidence_pct}% Match Confidence
                        </span>
                    </div>
                </div>

                <!-- Active Composition -->
                <div class="composition-line">
                    <strong>Active Formulation:</strong> ${r.salts_composition || r.generic_name || "Standard pharmaceutical composition"}
                </div>

                <!-- Metadata Grid -->
                <div class="meta-details-grid">
                    <div class="meta-item">
                        <span class="meta-label">Category</span>
                        <span class="meta-val">${r.category_name || "General Therapeutic"}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Packaging Form</span>
                        <span class="meta-val">${r.strip_size || "Blister pack"}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Prescription Class</span>
                        <span class="meta-val">${r.prescription_status || "Rx"}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Tablet Appearance</span>
                        <span class="meta-val">${r.tablet_color || "Standard"} • ${r.tablet_shape || "Solid unit"}</span>
                    </div>
                </div>

                <!-- Regulatory Warning -->
                ${isScheduleH ? `
                    <div class="schedule-warning-box">
                        <strong>${r.prescription_status} Prescription Drug Warning</strong>
                        To be sold by retail on the prescription of a Registered Medical Practitioner only. Do not consume without professional medical diagnosis.
                    </div>
                ` : ''}

                <!-- Matched Diagnostic Evidence -->
                ${clues ? `
                    <div class="matched-clues-section">
                        <span class="clues-title">Diagnostic Evidence:</span>
                        ${clues}
                    </div>
                ` : ''}

                <!-- Actions -->
                <div class="monograph-actions-row">
                    <button class="btn-view-detail" onclick="openDetailModal(${r.medicine_id})">
                        View Clinical Monograph
                    </button>
                    <button class="btn-view-alts" onclick="openAlternatives(${r.medicine_id}, '${r.brand_name.replace(/'/g, "\\'")}')">
                        Find Same-Salt Substitutes ↗
                    </button>
                </div>
            </article>
        `;
    });

    box.innerHTML = html;
}

// ── Detail Monograph Modal ───────────────────────────────────────────────────

async function openDetailModal(medicine_id) {
    const modal = document.getElementById("detailModal");
    const box = document.getElementById("detailModalContent");
    modal.style.display = "flex";
    box.innerHTML = `<div class="table-loading-notice">Retrieving clinical monograph…</div>`;

    try {
        const res = await fetch(`${API_BASE}/medicine/${medicine_id}`);
        const med = await res.json();

        if (med.detail) {
            box.innerHTML = `<p>Medicine not found.</p>`;
            return;
        }

        const isSchH = med.prescription_status && med.prescription_status.includes("Schedule");

        box.innerHTML = `
            <div class="monograph-modal-header">
                <div class="modal-brand-name">${med.brand_name} ${med.strength}</div>
                <div style="font-size:0.85rem; color:var(--slate-500); margin-top:2px;">
                    Manufactured by ${med.manufacturer_name || "—"} (${med.manufacturer_city || med.manufacturer_state || "India"})
                </div>
            </div>

            <div class="modal-section">
                <div class="modal-section-title">Active Pharmaceutical Ingredients</div>
                <div class="modal-section-content" style="font-size:0.95rem; font-weight:600; color:var(--brand-teal);">
                    ${med.salts_composition || med.generic_name || "—"}
                </div>
            </div>

            ${isSchH ? `
                <div class="schedule-warning-box" style="margin-bottom:16px;">
                    <strong>Indian Statutory Warning (${med.prescription_status})</strong>
                    Schedule H/H1 Drug: Caution — It is dangerous to take this preparation except in accordance with medical advice. Not to be dispensed without prescription.
                </div>
            ` : ''}

            <div class="modal-section">
                <div class="modal-section-title">Therapeutic Indication / Uses</div>
                <div class="modal-section-content">
                    ${med.uses || "Refer to manufacturer package insert for indicated therapeutic use."}
                </div>
            </div>

            <div class="modal-section">
                <div class="modal-section-title">Clinical Warnings & Precautions</div>
                <div class="modal-section-content">
                    ${med.warnings || "Consult a registered doctor before use. Do not exceed prescribed dosage."}
                </div>
            </div>

            <div class="modal-section">
                <div class="modal-section-title">Storage & Packaging</div>
                <div class="modal-section-content">
                    ${med.storage_info || "Store in a cool dry place. Protect from moisture and direct sunlight."}
                    <br><span style="color:var(--slate-500); font-size:0.8rem;">Packaging: ${med.strip_size || "Blister strip"} • Dominant Color: ${med.dominant_color || "Foil"}</span>
                </div>
            </div>

            <div class="modal-section" style="margin-top:20px; padding-top:14px; border-top:1px solid var(--slate-200);">
                <button class="btn-search-action" onclick="openAlternatives(${med.medicine_id}, '${med.brand_name.replace(/'/g, "\\'")}')">
                    View Generic Substitutes (Same Active Salt)
                </button>
            </div>
        `;
    } catch (e) {
        box.innerHTML = `<p>Error loading medicine details.</p>`;
    }
}

async function openAlternatives(medicine_id, brandName) {
    const modal = document.getElementById("detailModal");
    const box = document.getElementById("detailModalContent");
    modal.style.display = "flex";
    box.innerHTML = `<div class="table-loading-notice">Searching bio-equivalent formulations…</div>`;

    try {
        const res = await fetch(`${API_BASE}/alternatives/${medicine_id}`);
        const alts = await res.json();

        if (!alts || alts.length === 0) {
            box.innerHTML = `
                <div class="monograph-modal-header">
                    <div class="modal-brand-name">Substitutes for ${brandName}</div>
                </div>
                <p style="color:var(--slate-500); font-size:0.88rem;">
                    No other branded formulations with identical active composition were found in the current catalog.
                </p>
            `;
            return;
        }

        let rows = alts.map(a => `
            <tr>
                <td style="font-weight:600; color:var(--slate-900);">${a.brand_name} ${a.strength}</td>
                <td>${a.manufacturer_name || "—"}</td>
                <td style="font-family:var(--font-mono); font-size:0.75rem;">${a.salts_composition || a.shared_salts || "—"}</td>
                <td><span class="form-badge">${a.prescription_status || "Rx"}</span></td>
            </tr>
        `).join("");

        box.innerHTML = `
            <div class="monograph-modal-header">
                <div class="modal-brand-name">Generic Substitutes for ${brandName}</div>
                <div style="font-size:0.82rem; color:var(--slate-500); margin-top:2px;">
                    Formulations sharing identical active chemical compounds and dosage
                </div>
            </div>

            <div class="table-wrapper">
                <table class="clinical-data-table">
                    <thead>
                        <tr>
                            <th>Brand Formulation</th>
                            <th>Manufacturer</th>
                            <th>Active Composition</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    } catch (e) {
        box.innerHTML = `<p>Error loading alternatives.</p>`;
    }
}

function closeDetailModal() {
    document.getElementById("detailModal").style.display = "none";
}

function closeModal(event) {
    if (event.target === document.getElementById("detailModal")) {
        closeDetailModal();
    }
}

// ── DBMS Normalization & Schema Inspector ─────────────────────────────────────

async function loadNormalizationData() {
    switchNormView("unf");
}

async function switchNormView(mode) {
    const btnUNF = document.getElementById("btnUNF");
    const btnNorm = document.getElementById("btnNorm");
    const container = document.getElementById("normTableContainer");
    const explainer = document.getElementById("normExplanation");

    if (mode === "unf") {
        btnUNF.classList.add("active");
        btnNorm.classList.remove("active");
        explainer.innerHTML = `
            <div class="explainer-content">
                <strong>UNF (Unnormalized Flat Table):</strong>
                <span>
                    Violates First Normal Form (1NF). Multiple active ingredients are concatenated into a single cell ("Nimesulide 100mg, Paracetamol 325mg").
                    This causes repeating groups, prevents foreign key enforcement, and makes atomic chemical queries impossible.
                </span>
            </div>
        `;

        try {
            const res = await fetch(`${API_BASE}/unf`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const rows = data.rows || data;
            renderSimpleTable(rows, container, data.columns || null);
        } catch (e) {
            console.error("UNF load error:", e);
            container.innerHTML = `<div class="table-loading-notice">Unable to load UNF view. Backend may still be starting up — try again in a moment.</div>`;
        }
    } else {
        btnNorm.classList.add("active");
        btnUNF.classList.remove("active");
        explainer.innerHTML = `
            <div class="explainer-content">
                <strong>Third Normal Form (3NF Decomposed Schema):</strong>
                <span>
                    Decomposed into distinct relations: <code>Medicines</code>, <code>Manufacturers</code>, <code>Salts</code>, and 
                    <code>Medicine_Salt_Mapping</code> (Many-to-Many junction). Every attribute is atomic, depend purely on the primary key, and has zero transitive dependencies.
                </span>
            </div>
        `;

        try {
            const res = await fetch(`${API_BASE}/tables/Medicines`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const rows = data.rows || data;
            renderSimpleTable(rows, container, data.columns || null);
        } catch (e) {
            console.error("3NF load error:", e);
            container.innerHTML = `<div class="table-loading-notice">Unable to load 3NF table. Backend may still be starting up — try again in a moment.</div>`;
        }
    }
}

async function loadTable(tableName) {
    const container = document.getElementById("schemaTableContainer");
    document.getElementById("currentTableName").textContent = `Entity Table: ${tableName}`;

    // Highlight active button
    document.querySelectorAll("#paneTables .entity-btn").forEach(btn => {
        btn.classList.toggle("active", btn.textContent.trim().startsWith(tableName));
    });

    container.innerHTML = `<div class="table-loading-notice">Loading table records from SQLite…</div>`;

    try {
        const res = await fetch(`${API_BASE}/tables/${tableName}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const rows = data.rows || data;
        const cols = data.columns || (rows.length ? Object.keys(rows[0]) : []);
        // Show metadata header
        document.getElementById("currentTableName").textContent =
            `Entity Table: ${tableName}  (${rows.length} rows, ${cols.length} columns)`;
        renderSimpleTable(rows, container);
    } catch (e) {
        console.error(`Table ${tableName} load error:`, e);
        container.innerHTML = `<div class="table-loading-notice">Table ${tableName} could not be queried. Check backend is running at port 8000.</div>`;
    }
}

async function loadView(viewName) {
    const container = document.getElementById("viewsTableContainer");
    document.getElementById("currentViewName").textContent = `SQL View: ${viewName}`;

    // Highlight active button
    document.querySelectorAll("#paneViews .entity-btn").forEach(btn => {
        btn.classList.toggle("active", btn.textContent.trim().startsWith(viewName));
    });

    container.innerHTML = `<div class="table-loading-notice">Executing SQL view query…</div>`;

    try {
        const res = await fetch(`${API_BASE}/views/${viewName}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const rows = data.rows || data;
        const cols = data.columns || (rows.length ? Object.keys(rows[0]) : []);
        document.getElementById("currentViewName").textContent =
            `SQL View: ${viewName}  — ${data.description || ""}  (${rows.length} rows)`;
        renderSimpleTable(rows, container);
    } catch (e) {
        console.error(`View ${viewName} load error:`, e);
        container.innerHTML = `<div class="table-loading-notice">View ${viewName} could not be queried. Check backend is running at port 8000.</div>`;
    }
}

function renderSimpleTable(rows, container, specificCols = null) {
    if (!rows || rows.length === 0) {
        container.innerHTML = `<div class="table-loading-notice">No records found.</div>`;
        return;
    }

    const cols = specificCols || Object.keys(rows[0]);
    let thead = cols.map(c => `<th>${c.replace(/_/g, " ").toUpperCase()}</th>`).join("");
    let tbody = rows.slice(0, 30).map(r => {
        let tds = cols.map((c, i) => {
            let val = r[c] !== null && r[c] !== undefined ? String(r[c]) : "—";
            let cls = "";
            if (i === 0 && c.toLowerCase().includes("id")) cls = "cell-pk";
            if (c.includes("unf")) cls = "cell-anomaly";
            return `<td class="${cls}" title="${val}">${val}</td>`;
        }).join("");
        return `<tr>${tds}</tr>`;
    }).join("");

    container.innerHTML = `
        <table class="clinical-data-table">
            <thead><tr>${thead}</tr></thead>
            <tbody>${tbody}</tbody>
        </table>
    `;
}