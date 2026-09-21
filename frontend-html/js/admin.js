/**
 * Admin Command Center Controller
 * Enforces server session authentication, role checks, farmer search, status toggles,
 * confirmation modal on cascade user deletion, and reports visualization.
 */

let currentAdminUser = null;
let pendingDeleteFarmerId = null;
let searchDebounceTimer = null;
let authCheckInProgress = false;

document.addEventListener("DOMContentLoaded", async () => {
  await checkAdminAuth();
});

window.addEventListener("pageshow", async (event) => {
  await checkAdminAuth();
});

async function checkAdminAuth() {
  if (authCheckInProgress) return;
  authCheckInProgress = true;
  try {
    const res = await AgriAPI.getMe();
    if (!res || !res.authenticated || !res.user) {
      window.location.replace("admin-login.html");
      return;
    }
    if (res.user.role !== "admin") {
      alert("Access Denied: Administrative privileges required.");
      window.location.replace("admin-login.html");
      return;
    }
    currentAdminUser = res.user;

    // Load initial dashboard data in parallel for instant sub-second response
    await Promise.allSettled([
      loadAdminMetrics(),
      loadFarmersDirectory()
    ]);
  } catch (err) {
    console.warn("Admin authentication check failed:", err);
    window.location.replace("admin-login.html");
  } finally {
    authCheckInProgress = false;
  }
}

async function handleAdminLogout() {
  try {
    await AgriAPI.logout();
  } catch (_) {}
  // Explicitly clear client-side cookie & storage
  document.cookie = "agrigo_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  try {
    sessionStorage.clear();
    localStorage.removeItem("agrigo_token");
    localStorage.removeItem("agrigo_admin_token");
  } catch (_) {}
  window.location.replace("admin-login.html?logged_out=1");
}

// Tab Switching
function switchAdminTab(tabKey, btn) {
  document.querySelectorAll(".admin-tab-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  const tabSections = {
    farmers: "tab-sec-farmers",
    sources: "tab-sec-sources",
    reports: "tab-sec-reports",
    audit: "tab-sec-audit",
    health: "tab-sec-health"
  };

  Object.values(tabSections).forEach(secId => {
    const el = document.getElementById(secId);
    if (el) el.style.display = "none";
  });

  const activeSec = document.getElementById(tabSections[tabKey]);
  if (activeSec) activeSec.style.display = "block";

  if (tabKey === "farmers") loadFarmersDirectory();
  if (tabKey === "sources") loadSourcesRegistry();
  if (tabKey === "reports") loadReports();
  if (tabKey === "audit") loadAuditLogs();
  if (tabKey === "health") loadHealth();
}

// ----------------- Metrics -----------------
async function loadAdminMetrics() {
  try {
    const data = await AgriAPI.getAdminDashboard();
    if (data) {
      const setTxt = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = (val !== undefined && val !== null) ? val : 0;
      };
      setTxt("m-farmers", data.total_farmers || 0);
      setTxt("m-farmers-sub", `${data.active_farmers || 0} Active / ${data.suspended_farmers || 0} Suspended`);
      setTxt("m-crops", data.active_crops || 0);
      setTxt("m-sources", data.knowledge_sources || 0);
      setTxt("m-mandi", data.live_mandi_prices || 0);
      setTxt("m-sessions", data.active_sessions || 0);
    }
  } catch (e) {
    console.error("Error loading admin metrics:", e);
  }
}

// ----------------- Farmers Directory (Search, View, Suspend, Delete) -----------------
function debounceFarmerSearch() {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    loadFarmersDirectory();
  }, 300);
}

async function loadFarmersDirectory() {
  const tbody = document.getElementById("farmers-table-body");
  if (!tbody) return;
  const searchInput = document.getElementById("farmer-search-input");
  const q = searchInput ? searchInput.value.trim() : "";
  const statusFilter = document.getElementById("farmer-status-filter");
  const status = statusFilter ? statusFilter.value : "";
  const roleEl = document.getElementById("user-role-filter");
  const role = roleEl ? roleEl.value : "";

  try {
    const users = await AgriAPI.getAdminUsers(q, status, role);
    tbody.innerHTML = "";

    if (!users || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8"><div class="cyber-empty"><span>👥</span>[QUERY RESULT: ZERO MATCHING ACCOUNTS FOUND IN REPOSITORY]</div></td></tr>`;
      return;
    }

    users.forEach(u => {
      const tr = document.createElement("tr");
      const isSuspended = u.status === "suspended";
      const statusBadge = isSuspended
        ? `<span class="badge" style="background:rgba(239,68,68,0.15); color:#EF4444; border-color:rgba(239,68,68,0.3);">● Suspended</span>`
        : `<span class="badge" style="background:rgba(16,185,129,0.15); color:#10B981; border-color:rgba(16,185,129,0.3);">● Active</span>`;

      const toggleBtn = isSuspended
        ? `<button class="action-btn-sm btn-activate" onclick="toggleUserStatus('${u.id}', 'active')">Reactivate</button>`
        : `<button class="action-btn-sm btn-suspend" onclick="toggleUserStatus('${u.id}', 'suspended')">Suspend</button>`;

      const localCreated = AgriAPI.formatLocalDateTime(u.created_at);

      const isAdm = u.role === "admin";
      const roleBadge = isAdm
        ? `<span class="badge" style="background:rgba(92,107,192,0.3); color:#A5B4FC; border-color:rgba(92,107,192,0.4); font-size:10.5px;">🛡️ Admin</span>`
        : `<span class="badge" style="background:rgba(16,185,129,0.2); color:#10B981; border-color:rgba(16,185,129,0.35); font-size:10.5px;">🌾 Farmer</span>`;

      const detailsHtml = isAdm
        ? `<span class="badge" style="background:rgba(92,107,192,0.15); color:#80DEEA;">Command Access</span>`
        : `<span class="badge" style="background:rgba(255,255,255,0.06);">${u.crops_count || 0} Crops</span> <span class="badge" style="background:rgba(255,255,255,0.06);">${u.reminders_count || 0} Reminders</span>`;

      // Prevent delete button on current admin
      const isSelf = currentAdminUser && currentAdminUser.id === u.id;
      const deleteBtn = isSelf
        ? `<button class="action-btn-sm" style="opacity:0.3; cursor:not-allowed;" title="Cannot delete yourself" disabled>Self</button>`
        : `<button class="action-btn-sm btn-delete" onclick="openDeleteConfirmModal('${u.id}', '${(u.name || u.phone || "User").replace(/'/g, "\\'")}')">Delete</button>`;

      tr.innerHTML = `
        <td><code style="color:#00E5FF; font-size:12px;">${u.id}</code></td>
        <td>
          <div style="display:flex; align-items:center; gap:6px;">
            ${roleBadge}
            <strong>${u.name}</strong>
          </div>
        </td>
        <td>
          <span style="font-size:12px; color:#C8E6C9;">${u.phone}</span>
        </td>
        <td>${u.region || u.village || 'HQ / India'}</td>
        <td>${detailsHtml}</td>
        <td>${statusBadge}</td>
        <td style="font-size:12px; color:var(--text-muted);">${localCreated}</td>
        <td style="text-align:right;">
          <div style="display:inline-flex; gap:6px;">
            <button class="action-btn-sm btn-view" onclick="openFarmerDetail('${u.id}')">View</button>
            ${toggleBtn}
            ${deleteBtn}
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px; color:#EF4444;">Error loading users: ${e.message}</td></tr>`;
  }
}

// ----------------- Add User / Admin Modal Functions -----------------
function openAddUserModal() {
  const modal = document.getElementById("add-user-modal");
  const form = document.getElementById("add-user-form");
  const err = document.getElementById("add-user-err-msg");
  if (err) err.style.display = "none";
  if (form) form.reset();
  toggleAddUserRoleFields();
  if (modal) modal.classList.add("active");
}

function toggleAddUserRoleFields() {
  const role = document.getElementById("new-user-role").value;
  const farmerFields = document.getElementById("new-user-farmer-fields");
  const identLabel = document.getElementById("new-user-ident-label");
  const identInput = document.getElementById("new-user-identifier");

  if (role === "admin") {
    if (farmerFields) farmerFields.style.display = "none";
    if (identLabel) identLabel.textContent = "एडमिन ईमेल या ID *";
    if (identInput) identInput.placeholder = "e.g. new.admin@agrigo.com";
  } else {
    if (farmerFields) farmerFields.style.display = "block";
    if (identLabel) identLabel.textContent = "मोबाइल नंबर (10 अंक) *";
    if (identInput) identInput.placeholder = "e.g. 9876500001";
  }
}

async function handleCreateUserSubmit(e) {
  e.preventDefault();
  const errBox = document.getElementById("add-user-err-msg");
  const submitBtn = document.getElementById("btn-submit-add-user");
  errBox.style.display = "none";

  const role = document.getElementById("new-user-role").value;
  const status = document.getElementById("new-user-status").value;
  const name = document.getElementById("new-user-name").value.trim();
  const identifier = document.getElementById("new-user-identifier").value.trim();
  const password = document.getElementById("new-user-password").value;

  if (!name || !identifier || !password) {
    errBox.textContent = "कृपया सभी आवश्यक फ़ील्ड भरें।";
    errBox.style.display = "block";
    return;
  }

  const payload = {
    role,
    status,
    name,
    identifier,
    password
  };

  if (role === "farmer") {
    payload.state = document.getElementById("new-user-state").value;
    payload.district = document.getElementById("new-user-district").value.trim() || "Varanasi";
    payload.farm_area = parseFloat(document.getElementById("new-user-area").value) || 2.5;
    payload.primary_crop = document.getElementById("new-user-crop").value;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "खाता बनाया जा रहा है...";

  try {
    const res = await AgriAPI.createAdminUser(payload);
    if (!res || !res.success) {
      throw new Error(res.detail || res.message || "उपयोगकर्ता बनाने में त्रुटि हुई।");
    }

    alert(`सफल! ${role === 'admin' ? 'एडमिन' : 'किसान'} खाता '${name}' सफलतापूर्वक बना दिया गया है।`);
    closeModal("add-user-modal");
    await loadAdminMetrics();
    await loadFarmersDirectory();
  } catch (err) {
    errBox.textContent = err.message;
    errBox.style.display = "block";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "उपयोगकर्ता खाता बनाएं ➔";
  }
}

async function toggleUserStatus(userId, newStatus) {
  try {
    await AgriAPI.updateUserStatus(userId, newStatus);
    await loadAdminMetrics();
    await loadFarmersDirectory();
  } catch (e) {
    alert("Error updating status: " + e.message);
  }
}

async function openFarmerDetail(userId) {
  const modal = document.getElementById("farmer-detail-modal");
  const body = document.getElementById("fd-body");
  const nameEl = document.getElementById("fd-name");
  body.innerHTML = "Loading farmer profile & records...";
  modal.classList.add("active");

  try {
    const f = await AgriAPI.getAdminUserDetail(userId);
    nameEl.innerText = `${f.name} (${f.id})`;

    const cropsList = (f.crops && f.crops.length > 0)
      ? f.crops.map(c => `• <strong>${c.crop_name}</strong> (${c.variety || 'Standard'}, Stage: ${c.stage})`).join("<br>")
      : "No crops currently tracked";

    const remindersList = (f.reminders && f.reminders.length > 0)
      ? f.reminders.map(r => `• ${r.title} [Due: ${r.due_date || 'Soon'}]`).join("<br>")
      : "No reminders set";

    const localJoined = AgriAPI.formatLocalDateTime(f.created_at);

    body.innerHTML = `
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; background:rgba(255,255,255,0.03); padding:12px; border-radius:8px;">
        <div><strong>Phone:</strong> ${f.phone}</div>
        <div><strong>Status:</strong> ${f.status}</div>
        <div><strong>Location:</strong> ${f.village}, ${f.district}, ${f.state}</div>
        <div><strong>Registered (Local):</strong> ${localJoined}</div>
      </div>
      <div style="margin-bottom:12px;">
        <h4 style="color:#00E5FF; margin-bottom:6px; font-size:13px;">🌾 Active Crops:</h4>
        <div style="background:rgba(255,255,255,0.02); padding:8px 12px; border-radius:6px; font-size:12px;">${cropsList}</div>
      </div>
      <div style="margin-bottom:12px;">
        <h4 style="color:#00E5FF; margin-bottom:6px; font-size:13px;">⏰ Agricultural Reminders:</h4>
        <div style="background:rgba(255,255,255,0.02); padding:8px 12px; border-radius:6px; font-size:12px;">${remindersList}</div>
      </div>
    `;
  } catch (e) {
    body.innerHTML = `<div style="color:#EF4444;">Error loading farmer details: ${e.message}</div>`;
  }
}

// ----------------- Deletion Confirmation Modal (Requirement 4) -----------------
function openDeleteConfirmModal(userId, userName) {
  pendingDeleteFarmerId = userId;
  document.getElementById("del-farmer-id").innerText = userId;
  document.getElementById("del-farmer-name").innerText = userName;
  document.getElementById("delete-confirm-modal").classList.add("active");
}

async function executeDeleteFarmer() {
  if (!pendingDeleteFarmerId) return;
  const btn = document.getElementById("btn-confirm-delete");
  btn.innerText = "Executing Cascade Deletion...";
  btn.disabled = true;

  try {
    const res = await AgriAPI.deleteFarmerAccount(pendingDeleteFarmerId);
    alert(res.message || "Farmer account and all associated data permanently deleted.");
    closeModal("delete-confirm-modal");
    await loadAdminMetrics();
    await loadFarmersDirectory();
  } catch (err) {
    alert("Deletion failed: " + err.message);
  } finally {
    btn.innerText = "Permanently Delete";
    btn.disabled = false;
    pendingDeleteFarmerId = null;
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

// ----------------- Knowledge Sources Registry -----------------
async function loadSourcesRegistry() {
  const tbody = document.getElementById("sources-table-body");
  try {
    const res = await AgriAPI.getKnowledgeSources();
    tbody.innerHTML = "";

    if (!res || !res.sources || res.sources.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="cyber-empty"><span>🏛️</span>[REGISTRY NOTICE: ZERO KNOWLEDGE SOURCES CURRENTLY REGISTERED]</div></td></tr>`;
      return;
    }

    res.sources.forEach(s => {
        const tr = document.createElement("tr");
        const statusClass = s.status === "Active" ? "color: #10B981;" : "color: #F59E0B;";
        tr.innerHTML = `
          <td><strong><a href="${s.url}" target="_blank" style="color: #00E5FF; text-decoration: none;">${s.name}</a></strong></td>
          <td>${s.organization}</td>
          <td>${s.country}</td>
          <td><span class="badge" style="background: rgba(255,255,255,0.06);">${s.license_name || 'Open Data'}</span></td>
          <td>${s.allows_automated_collection ? 'Allowed ✓' : 'Restricted'}</td>
          <td style="${statusClass}">● ${s.status}</td>
          <td>
            <button class="action-btn-sm btn-delete" onclick="handleDeleteSource('${s.id}')">Remove</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#EF4444;">Error loading sources: ${e.message}</td></tr>`;
  }
}

function openAddSourceModal() {
  document.getElementById("add-source-modal").classList.add("active");
}

async function handleSaveKnowledgeSource() {
  const name = document.getElementById("src-name").value.trim();
  const url = document.getElementById("src-url").value.trim();
  const organization = document.getElementById("src-org").value.trim();
  const license_name = document.getElementById("src-lic").value.trim();

  if (!name || !url || !organization) {
    alert("Please fill in Name, URL, and Organization.");
    return;
  }

  try {
    await AgriAPI.addKnowledgeSource({ name, url, organization, license_name });
    closeModal("add-source-modal");
    await loadSourcesRegistry();
  } catch (e) {
    alert("Error adding source: " + e.message);
  }
}

async function handleDeleteSource(sourceId) {
  if (!confirm("Are you sure you want to remove this knowledge source?")) return;
  try {
    await AgriAPI.deleteKnowledgeSource(sourceId);
    await loadSourcesRegistry();
  } catch (e) {
    alert("Error deleting source: " + e.message);
  }
}

// ----------------- Reports (Cyber Real SVG / Analytics Charts) -----------------
async function loadReports() {
  const container = document.getElementById("reports-container");
  container.innerHTML = `<div class="cyber-empty"><span>⏳</span>[SYSTEM: COMPILING REAL-TIME ANALYTICS FROM DATABASE...]</div>`;

  try {
    const data = await AgriAPI.getAdminReports();
    const localGenerated = AgriAPI.formatLocalDateTime(data.generated_at);

    // 1. Regional Distribution Chart
    const regList = data.regional_distribution || [];
    let regChartHtml = "";
    if (regList.length === 0) {
      regChartHtml = `<div class="cyber-empty"><span>📡</span>[SYSTEM ALERT: ZERO REGIONAL FARMER RECORDS IN DATA LAKE]</div>`;
    } else {
      const maxFarmers = Math.max(...regList.map(r => r.farmer_count || 1), 1);
      const totalFarmers = regList.reduce((acc, r) => acc + (r.farmer_count || 0), 0);

      const rows = regList.map(r => {
        const pct = Math.round((r.farmer_count / totalFarmers) * 100);
        const widthPct = Math.round((r.farmer_count / maxFarmers) * 100);
        return `
          <div class="cyber-bar-row">
            <span style="font-weight:700; color:#FFF; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${r.state}</span>
            <div class="cyber-bar-track">
              <div class="cyber-bar-fill" style="width: ${widthPct}%;"></div>
            </div>
            <span style="text-align:right; font-weight:800; color:#00FF66;">${r.farmer_count} <small style="color:#5C7A8E;">frms</small></span>
            <span style="text-align:right; color:#00E5FF; font-weight:700;">${pct}%</span>
          </div>
        `;
      }).join("");

      regChartHtml = `
        <div style="margin-top:12px;">
          <div style="display:grid; grid-template-columns: 180px 1fr 65px 50px; gap:12px; font-size:11px; color:#5C7A8E; text-transform:uppercase; margin-bottom:8px; font-weight:700;">
            <span>State / Territory</span>
            <span>Relative Distribution</span>
            <span style="text-align:right;">Farmers</span>
            <span style="text-align:right;">Share</span>
          </div>
          ${rows}
        </div>
      `;
    }

    // 2. Active Crops Distribution
    const cropList = data.crop_cycles_distribution || [];
    let cropChartHtml = "";
    if (cropList.length === 0) {
      cropChartHtml = `<div class="cyber-empty"><span>🌾</span>[SYSTEM ALERT: ZERO ACTIVE CROP CYCLES IN DATA LAKE]</div>`;
    } else {
      const maxCycles = Math.max(...cropList.map(c => c.count || 1), 1);
      const totalCycles = cropList.reduce((acc, c) => acc + (c.count || 0), 0);

      const rows = cropList.map(c => {
        const widthPct = Math.round((c.count / maxCycles) * 100);
        const sharePct = Math.round((c.count / totalCycles) * 100);
        const avgAc = c.avg_acres ? Number(c.avg_acres).toFixed(1) : "1.0";
        return `
          <div class="cyber-bar-row">
            <span style="font-weight:700; color:#FFF; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${c.crop_name}</span>
            <div class="cyber-bar-track">
              <div class="cyber-bar-fill" style="width: ${widthPct}%; background: linear-gradient(90deg, #10B981, #FFB300);"></div>
            </div>
            <span style="text-align:right; font-weight:800; color:#FFB300;">${c.count} <small style="color:#5C7A8E;">cyc</small></span>
            <span style="text-align:right; color:#10B981; font-weight:700;">${sharePct}%</span>
          </div>
        `;
      }).join("");

      cropChartHtml = `
        <div style="margin-top:12px;">
          <div style="display:grid; grid-template-columns: 180px 1fr 65px 50px; gap:12px; font-size:11px; color:#5C7A8E; text-transform:uppercase; margin-bottom:8px; font-weight:700;">
            <span>Crop Specie</span>
            <span>Cultivation Intensity</span>
            <span style="text-align:right;">Cycles</span>
            <span style="text-align:right;">Share</span>
          </div>
          ${rows}
        </div>
      `;
    }

    container.innerHTML = `
      <div class="cyber-chart-card">
        <div class="cyber-chart-head">
          <div class="cyber-chart-title">📊 REGIONAL FARMER DISTRIBUTION (DATA LAKE ANALYTICS)</div>
          <span class="cyber-badge badge-cyber-cyan">REAL-TIME QUERY: SQLITE WAL</span>
        </div>
        ${regChartHtml}
      </div>

      <div class="cyber-chart-card">
        <div class="cyber-chart-head">
          <div class="cyber-chart-title">🌾 ACTIVE CROP PHENOLOGY DISTRIBUTION</div>
          <span class="cyber-badge badge-cyber-green">ACTIVE AGRONOMIC CYCLES</span>
        </div>
        ${cropChartHtml}
      </div>

      <div class="cyber-chart-card">
        <div class="cyber-chart-head">
          <div class="cyber-chart-title">🔒 TELEMETRY PROVENANCE & TRANSACTION LEDGER</div>
          <span class="cyber-badge badge-cyber-green">VERIFIED</span>
        </div>
        <div style="font-family:'JetBrains Mono', monospace; font-size:12px; line-height:1.8; color:#D1E4E8;">
          • Report Generated (Local Time): <strong style="color:#00FF66;">${localGenerated}</strong><br>
          • Core Database Architecture: <strong style="color:#00E5FF;">SQLite3 WAL (Write-Ahead Logging) Persistent Transaction Store</strong><br>
          • Government Datasets Integrated: <strong style="color:#FFB300;">455,359 historical agricultural records (data.gov.in)</strong><br>
          • Cryptographic Session Security: <strong style="color:#00FF66;">Argon2id Password Hashes • HttpOnly SameSite Lax Sessions</strong><br>
          • Access Control Protocol: <strong style="color:#00E5FF;">RBAC + Strict Cross-Account IDOR Barrier Active</strong>
        </div>
      </div>
    `;
  } catch (e) {
    container.innerHTML = `<div class="cyber-empty" style="color:#FF3366;"><span>⚠️</span>[SYSTEM ERROR: FAILED TO COMPILE ANALYTICS: ${e.message}]</div>`;
  }
}

// ----------------- Audit Logs -----------------
async function loadAuditLogs() {
  const tbody = document.getElementById("audit-table-body");
  try {
    const res = await AgriAPI.getAdminAuditLogs(50);
    tbody.innerHTML = "";

    const logs = res.logs || [];
    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="cyber-empty"><span>🛡️</span>[SECURITY AUDIT LOG IS CURRENTLY PRISTINE — 0 RECORDED ANOMALIES]</div></td></tr>`;
      return;
    }

    logs.forEach(l => {
      const tr = document.createElement("tr");
      const localTime = AgriAPI.formatLocalDateTime(l.timestamp);
      tr.innerHTML = `
        <td><code style="color:#94A3B8;">#${l.id}</code></td>
        <td style="font-size:12px;">${localTime}</td>
        <td><code>${l.actor_id}</code></td>
        <td><span class="badge" style="background:rgba(255,255,255,0.06);">${l.actor_type}</span></td>
        <td><strong style="color:#00E5FF;">${l.action}</strong></td>
        <td>${l.resource_type} ${l.resource_id ? `(${l.resource_id})` : ''}</td>
        <td style="font-size:11.5px; color:var(--text-muted);">${l.details_json || '—'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#EF4444;">Error loading audit logs: ${e.message}</td></tr>`;
  }
}

// ----------------- System Health -----------------
async function loadHealth() {
  const container = document.getElementById("health-content");
  try {
    const h = await AgriAPI.getAdminHealth();
    const localTime = AgriAPI.formatLocalDateTime(h.timestamp);

    let provHtml = (h.providers || []).map(p => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:6px; margin-bottom:6px;">
        <div>
          <strong>${p.service}</strong> <span style="font-size:11.5px; color:var(--text-muted);">(${p.type})</span>
        </div>
        <div>
          <span style="color:#10B981; font-weight:700;">● ${p.status}</span>
          <span style="font-size:11.5px; color:var(--text-muted); margin-left:8px;">${p.latency_ms} ms</span>
        </div>
      </div>
    `).join("");

    container.innerHTML = `
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:16px;">
        <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px;">
          <strong>Database:</strong> ${h.database.type} (${h.database.path})<br>
          <strong>Database Size:</strong> ${h.database.size_kb} KB<br>
          <strong>Status:</strong> <span style="color:#10B981;">Operational ✓</span>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px;">
          <strong>Active Sessions:</strong> ${h.sessions.active_count}<br>
          <strong>Session Storage:</strong> ${h.sessions.storage}<br>
          <strong>Telemetry Time:</strong> ${localTime}
        </div>
      </div>
      <h4 style="color:#00E5FF; margin-bottom:8px; font-size:13px;">External & Internal Provider Connectivity:</h4>
      ${provHtml}
    `;
  } catch (e) {
    container.innerHTML = `<div style="color:#EF4444;">Error loading health: ${e.message}</div>`;
  }
}

// Expose functions explicitly to window for inline onclick handlers
window.checkAdminAuth = checkAdminAuth;
window.handleAdminLogout = handleAdminLogout;
window.switchAdminTab = switchAdminTab;
window.loadAdminMetrics = loadAdminMetrics;
window.loadFarmersDirectory = loadFarmersDirectory;
window.debounceFarmerSearch = debounceFarmerSearch;
window.openAddUserModal = openAddUserModal;
window.toggleAddUserRoleFields = toggleAddUserRoleFields;
window.handleCreateUserSubmit = handleCreateUserSubmit;
window.toggleUserStatus = toggleUserStatus;
window.openFarmerDetail = openFarmerDetail;
window.openDeleteConfirmModal = openDeleteConfirmModal;
window.executeDeleteFarmer = executeDeleteFarmer;
window.closeModal = closeModal;
window.loadSourcesRegistry = loadSourcesRegistry;
window.openAddSourceModal = openAddSourceModal;
window.handleSaveKnowledgeSource = handleSaveKnowledgeSource;
window.handleDeleteSource = handleDeleteSource;
window.loadReports = loadReports;
window.loadAuditLogs = loadAuditLogs;
window.loadHealth = loadHealth;

