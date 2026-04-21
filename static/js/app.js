/* AuStudyFinder — Frontend Logic */

const API = {
  search: (params) => `/api/search?${new URLSearchParams(params)}`,
  course: (code) => `/api/course/${encodeURIComponent(code)}`,
  packages: (code) => `/api/packages/${encodeURIComponent(code)}`,
  filters: () => `/api/filters`,
  scholarships: (params) => `/api/scholarships?${new URLSearchParams(params)}`,
  stats: () => `/api/stats`,
};

let currentPage = 1;
let currentQuery = {};
let debounceTimer = null;

// ── INIT ────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadFilters();
  loadScholarships();
  setupNav();
  setupSearch();
  setupFilters();
  setupModal();
  setupQuickSearch();
});

// ── NAV TABS ────────────────────────────────────────────────
function setupNav() {
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const tab = link.dataset.tab;
      document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
      document.querySelectorAll(".tab-section").forEach((s) => s.classList.remove("active"));
      link.classList.add("active");
      document.getElementById(`tab-${tab}`).classList.add("active");
    });
  });
}

// ── STATS ────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res = await fetch(API.stats());
    const data = await res.json();
    document.getElementById("statCourses").textContent = data.courses.toLocaleString();
    document.getElementById("statInst").textContent = data.institutions.toLocaleString();
    document.getElementById("statStates").textContent = data.states;
    document.getElementById("statScholarships").textContent = data.scholarships;
  } catch (e) {}
}

// ── FILTERS ─────────────────────────────────────────────────
async function loadFilters() {
  try {
    const res = await fetch(API.filters());
    const data = await res.json();

    populateSelect("filterLevel", data.levels);
    populateSelect("filterField", data.fields.map((f) => ({
      value: f,
      label: f.replace(/^\d+ - /, ""),
    })));
    populateSelect("filterState", data.states.map((s) => ({
      value: s,
      label: stateFullName(s),
    })));

    // Scholarship level filter
    const slFilter = document.getElementById("scholarshipLevelFilter");
    data.levels.forEach((l) => {
      const opt = document.createElement("option");
      opt.value = l; opt.textContent = l;
      slFilter.appendChild(opt);
    });
    slFilter.addEventListener("change", loadScholarships);
  } catch (e) {}
}

function populateSelect(id, items) {
  const sel = document.getElementById(id);
  items.forEach((item) => {
    const opt = document.createElement("option");
    if (typeof item === "string") {
      opt.value = item; opt.textContent = item;
    } else {
      opt.value = item.value; opt.textContent = item.label;
    }
    sel.appendChild(opt);
  });
}

function stateFullName(code) {
  const map = { ACT: "ACT — Canberra", NSW: "NSW — Sydney", NT: "NT — Darwin", QLD: "QLD — Brisbane", SA: "SA — Adelaide", TAS: "TAS — Hobart", VIC: "VIC — Melbourne", WA: "WA — Perth" };
  return map[code] || code;
}

// ── SEARCH ──────────────────────────────────────────────────
function setupSearch() {
  const input = document.getElementById("searchInput");
  const btn = document.getElementById("searchBtn");

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch(1);
  });
  btn.addEventListener("click", () => doSearch(1));

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (input.value.length > 2) doSearch(1);
    }, 500);
  });
}

function setupFilters() {
  ["filterLevel", "filterField", "filterState", "filterMaxFee", "filterDuration", "filterExpired"].forEach((id) => {
    document.getElementById(id).addEventListener("change", () => doSearch(1));
  });
  document.getElementById("clearFilters").addEventListener("click", clearFilters);
}

function setupQuickSearch() {
  document.querySelectorAll(".quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("searchInput").value = btn.dataset.q;
      doSearch(1);
    });
  });
}

function clearFilters() {
  ["filterLevel", "filterField", "filterState", "filterMaxFee", "filterDuration"].forEach((id) => {
    document.getElementById(id).value = "";
  });
  document.getElementById("filterExpired").value = "No";
  doSearch(1);
}

async function doSearch(page) {
  currentPage = page;
  const q = document.getElementById("searchInput").value.trim();
  const params = {
    q,
    level: document.getElementById("filterLevel").value,
    field: document.getElementById("filterField").value,
    state: document.getElementById("filterState").value,
    expired: document.getElementById("filterExpired").value,
    page,
  };
  const maxFee = document.getElementById("filterMaxFee").value;
  if (maxFee) params.max_fee = maxFee;
  const duration = document.getElementById("filterDuration").value;
  if (duration) params.duration = duration;

  currentQuery = params;

  showLoading();

  try {
    const res = await fetch(API.search(params));
    const data = await res.json();
    renderResults(data);
  } catch (e) {
    document.getElementById("resultsGrid").innerHTML = `<div class="empty-state"><h3>Error loading results</h3><p>Please make sure the server is running.</p></div>`;
  }
}

function showLoading() {
  document.getElementById("resultsGrid").innerHTML = `<div class="loading-spinner"><div class="spinner"></div>Searching...</div>`;
  document.getElementById("resultsHeader").innerHTML = "";
  document.getElementById("pagination").innerHTML = "";
}

function renderResults(data) {
  const grid = document.getElementById("resultsGrid");
  const header = document.getElementById("resultsHeader");

  if (data.total === 0) {
    grid.innerHTML = `<div class="empty-state"><h3>No courses found</h3><p>Try different keywords or clear some filters.</p></div>`;
    header.innerHTML = "";
    document.getElementById("pagination").innerHTML = "";
    return;
  }

  const from = (data.page - 1) * data.per_page + 1;
  const to = Math.min(data.page * data.per_page, data.total);
  header.innerHTML = `Showing <strong>${from}–${to}</strong> of <strong>${data.total.toLocaleString()}</strong> courses`;

  grid.innerHTML = data.results.map(renderCourseCard).join("");

  // Attach click handlers
  grid.querySelectorAll(".course-card").forEach((card) => {
    card.addEventListener("click", () => openCourseModal(card.dataset.code));
  });

  renderPagination(data);
}

function renderCourseCard(c) {
  const expired = c.expired === "Yes" ? `<span class="tag tag-expired">Expired</span>` : "";
  const states = (c.states || []).map((s) => `<span class="tag tag-state">${s}</span>`).join("");
  const level = c.course_level ? `<span class="tag tag-level">${c.course_level}</span>` : "";
  const field = c.field_broad ? `<span class="tag tag-field">${c.field_broad.replace(/^\d+ - /, "")}</span>` : "";

  return `
    <div class="course-card" data-code="${esc(c.cricos_course_code)}">
      <div class="card-left">
        <div class="course-code">CRICOS ${esc(c.cricos_course_code || "")}</div>
        <div class="course-name">${esc(c.course_name || "")}</div>
        <div class="institution-name">🏛 ${esc(c.institution_name || "")}</div>
        <div class="card-tags">${level}${field}${states}${expired}</div>
      </div>
      <div class="card-right">
        <div class="card-fee">${esc(c.fee_formatted || "N/A")}</div>
        <div class="card-fee-label">Est. Total Cost</div>
        <div class="card-duration">⏱ ${esc(c.duration_formatted || "N/A")}</div>
      </div>
    </div>`;
}

function renderPagination(data) {
  const pg = document.getElementById("pagination");
  if (data.total_pages <= 1) { pg.innerHTML = ""; return; }

  const pages = [];
  const cur = data.page;
  const total = data.total_pages;

  pages.push(makePageBtn("← Prev", cur - 1, cur === 1));

  const range = getPageRange(cur, total);
  let lastPage = 0;
  range.forEach((p) => {
    if (p - lastPage > 1) pages.push(`<span style="padding:0 4px;color:#6b7280">…</span>`);
    pages.push(makePageBtn(p, p, false, p === cur));
    lastPage = p;
  });

  pages.push(makePageBtn("Next →", cur + 1, cur === total));
  pg.innerHTML = pages.join("");
  pg.querySelectorAll(".page-btn:not(:disabled)").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = parseInt(btn.dataset.page);
      if (!isNaN(p)) { doSearch(p); window.scrollTo({ top: 300, behavior: "smooth" }); }
    });
  });
}

function getPageRange(cur, total) {
  const delta = 2;
  const range = new Set([1, total]);
  for (let i = Math.max(2, cur - delta); i <= Math.min(total - 1, cur + delta); i++) range.add(i);
  return [...range].sort((a, b) => a - b);
}

function makePageBtn(label, page, disabled, active = false) {
  return `<button class="page-btn${active ? " active" : ""}" data-page="${page}" ${disabled ? "disabled" : ""}>${label}</button>`;
}

// ── MODAL ───────────────────────────────────────────────────
function setupModal() {
  document.getElementById("modalClose").addEventListener("click", closeModal);
  document.getElementById("modalOverlay").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeModal();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
}

async function openCourseModal(code) {
  const overlay = document.getElementById("modalOverlay");
  const content = document.getElementById("modalContent");

  overlay.classList.add("open");
  content.innerHTML = `<div class="loading-spinner"><div class="spinner"></div>Loading details...</div>`;

  try {
    const [courseRes, pkgRes] = await Promise.all([
      fetch(API.course(code)),
      fetch(API.packages(code)),
    ]);
    const c = await courseRes.json();
    const packages = pkgRes.ok ? await pkgRes.json() : [];
    content.innerHTML = renderCourseDetail(c, packages);
  } catch (e) {
    content.innerHTML = `<p>Failed to load course details.</p>`;
  }
}

function closeModal() {
  document.getElementById("modalOverlay").classList.remove("open");
}

function renderPackageCard(p) {
  const chain = p.chain;
  const totalCost = p.total_cost > 0
    ? `AUD $${Number(p.total_cost).toLocaleString("en-AU", { maximumFractionDigits: 0 })}`
    : "N/A";

  const courseItems = chain.map((cr, i) => {
    const isFirst = i === 0;
    const badgeClass = isFirst ? "current" : "companion";
    const badgeLabel = isFirst ? "CURRENT" : esc(cr.course_level || "");
    const plus = i > 0 ? `<div class="package-plus">+</div>` : "";
    return `${plus}
      <div class="package-course-item">
        <span class="package-badge ${badgeClass}">${badgeLabel}</span>
        <span class="package-course-name">${esc(cr.course_name || "")}</span>
        <span class="package-dur">${esc(cr.duration_formatted || "")}</span>
      </div>`;
  }).join("");

  const creditNote = p.diploma_credit
    ? `<div class="pkg-credit-note">📋 1-year credit applied — Diploma gives advanced standing into the Bachelor degree</div>`
    : "";

  return `
    <div class="package-card">
      <div class="package-courses">${courseItems}</div>
      ${creditNote}
      <div class="package-summary">
        <div class="package-total-dur">⏱ Total: <strong>${esc(p.total_formatted)}</strong></div>
        <div class="package-total-cost">💰 Est. Combined Cost: <strong>${totalCost}</strong></div>
      </div>
    </div>`;
}

function renderCourseDetail(c, packages = []) {
  const locs = (c.locations || []);
  const locHtml = locs.length
    ? locs.map((l) => `<div class="location-chip"><strong>${esc(l.location_state || "")}</strong> — ${esc(l.location_city || l.location_name || "")}</div>`).join("")
    : "<p style='color:#6b7280;font-size:14px'>No location data available.</p>";

  const inst = c.institution || {};
  const website = inst.website ? `<a href="${ensureHttp(inst.website)}" class="website-link" target="_blank">🌐 ${esc(inst.website)}</a>` : "";

  const boolTag = (val, label) => val === "Yes"
    ? `<span class="tag tag-field">✓ ${label}</span>`
    : `<span class="tag" style="background:#f3f4f6;color:#6b7280">✗ ${label}</span>`;

  // Google scholarship search button
  const scholarshipQuery = encodeURIComponent(`"${c.course_name}" scholarship Australia international student`);
  const scholarshipBtn = `<a href="https://www.google.com/search?q=${scholarshipQuery}" target="_blank" rel="noopener" class="scholarship-google-btn">🎓 Search Scholarships on Google</a>`;

  // Package recommendations
  const VET_LEVELS = ["Certificate I","Certificate II","Certificate III","Certificate IV","Diploma","Advanced Diploma","Vocational Short Course"];
  const isVET = VET_LEVELS.includes(c.course_level);
  let packagesHtml = "";
  if (isVET) {
    if (packages.length === 0) {
      packagesHtml = `
        <div class="modal-section-title">📦 Study Pathway Packages</div>
        <p style="color:#6b7280;font-size:14px">No pathway packages found at this institution in the same field of study.</p>`;
    } else {
      const pkgCards = packages.map((p) => renderPackageCard(p)).join("");
      packagesHtml = `
        <div class="modal-section-title">📦 Study Pathway Packages <span class="pkg-badge-info">Same institution · Same field · Higher level</span></div>
        <p style="color:#6b7280;font-size:13px;margin-bottom:12px">Progressive study pathways at <strong>${esc(c.institution_name)}</strong> — each step moves to a higher qualification in the same field.</p>
        <div class="packages-list">${pkgCards}</div>`;
    }
  }

  return `
    <div class="modal-course-code">CRICOS Course Code: ${esc(c.cricos_course_code || "")}</div>
    <div class="modal-course-name">${esc(c.course_name || "")}</div>
    <div class="modal-institution">🏛 ${esc(c.institution_name || "")}</div>

    <div class="modal-tags">
      ${c.course_level ? `<span class="tag tag-level">${esc(c.course_level)}</span>` : ""}
      ${c.field_broad ? `<span class="tag tag-field">${esc(c.field_broad.replace(/^\d+ - /, ""))}</span>` : ""}
      ${c.expired === "Yes" ? `<span class="tag tag-expired">Expired</span>` : `<span class="tag tag-level">Active</span>`}
      ${boolTag(c.work_component, "Work Component")}
      ${boolTag(c.dual_qualification, "Dual Qualification")}
      ${boolTag(c.foundation_studies, "Foundation Studies")}
    </div>

    <div class="modal-grid">
      <div class="modal-field">
        <div class="modal-field-label">Estimated Total Cost</div>
        <div class="modal-field-value big">${esc(c.fee_formatted || "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Tuition Fee</div>
        <div class="modal-field-value big">${esc(c.tuition_formatted || "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Non-Tuition Fee</div>
        <div class="modal-field-value">${esc(c.non_tuition_formatted || "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Duration</div>
        <div class="modal-field-value">${esc(c.duration_formatted || "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Language of Instruction</div>
        <div class="modal-field-value">${esc(c.course_language || "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">VET National Code</div>
        <div class="modal-field-value">${esc(c.vet_national_code || "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Narrow Field</div>
        <div class="modal-field-value">${esc(c.field_narrow ? c.field_narrow.replace(/^\d+ - /, "") : "N/A")}</div>
      </div>
      <div class="modal-field">
        <div class="modal-field-label">Provider Code</div>
        <div class="modal-field-value">${esc(c.cricos_provider_code || "N/A")}</div>
      </div>
    </div>

    <div class="modal-section-title">📍 Campus Locations</div>
    <div class="modal-locations">${locHtml}</div>

    ${inst.website ? `<div class="modal-section-title">🏛 Institution</div>
      <div class="modal-field-value">${esc(inst.institution_name || c.institution_name || "")}</div>
      <div style="margin-top:6px">${website}</div>` : ""}

    ${packagesHtml}

    <div class="modal-section-title">🎓 Scholarship Search</div>
    <p style="color:#6b7280;font-size:13px;margin-bottom:12px">Find scholarships related to this course on Google.</p>
    ${scholarshipBtn}
  `;
}

// ── SCHOLARSHIPS ────────────────────────────────────────────
async function loadScholarships() {
  const q = document.getElementById("scholarshipSearch")?.value || "";
  const level = document.getElementById("scholarshipLevelFilter")?.value || "";

  try {
    const res = await fetch(API.scholarships({ q, level }));
    const data = await res.json();
    renderScholarships(data);
  } catch (e) {}
}

function renderScholarships(scholarships) {
  const grid = document.getElementById("scholarshipsGrid");
  if (!scholarships.length) {
    grid.innerHTML = `<div class="empty-state"><h3>No scholarships found</h3><p>Try different search terms.</p></div>`;
    return;
  }
  grid.innerHTML = scholarships.map(renderScholarshipCard).join("");
}

function renderScholarshipCard(s) {
  const levels = s.level.includes("All levels") ? "All Levels" : s.level.join(", ");
  const tags = s.tags.map((t) => `<span class="scholarship-tag">${esc(t)}</span>`).join("");

  return `
    <div class="scholarship-card">
      <div class="scholarship-provider">${esc(s.provider)}</div>
      <div class="scholarship-name">${esc(s.name)}</div>
      <div class="scholarship-value">💰 ${esc(s.value)}</div>
      <div class="scholarship-desc">${esc(s.description)}</div>
      <div class="scholarship-eligibility"><strong>Eligibility:</strong> ${esc(s.eligibility)}</div>
      <div class="scholarship-eligibility"><strong>Study Level:</strong> ${esc(levels)}</div>
      <div class="scholarship-tags">${tags}</div>
      <a href="${esc(s.link)}" class="scholarship-link" target="_blank" rel="noopener">Visit Official Site →</a>
    </div>`;
}

// Setup scholarship search
document.addEventListener("DOMContentLoaded", () => {
  const ss = document.getElementById("scholarshipSearch");
  if (ss) {
    ss.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(loadScholarships, 400);
    });
  }
});

// ── UTILS ────────────────────────────────────────────────────
function esc(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function ensureHttp(url) {
  if (!url) return "#";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return "https://" + url;
}
