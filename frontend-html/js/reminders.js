/**
 * AgriGo Reminder Dashboard Controller (Vanilla JS)
 * Production Session Authentication & IDOR Verification
 */

let allReminders = [];
let currentFilter = "all";
let currentFarmerUser = null;

document.addEventListener("DOMContentLoaded", async () => {
  await checkFarmerAuth();
});

window.addEventListener("pageshow", async (event) => {
  await checkFarmerAuth();
});

async function checkFarmerAuth() {
  try {
    const meRes = await AgriAPI.getMe();
    if (!meRes || !meRes.authenticated || !meRes.user) {
      window.location.href = "farmer-login.html";
      return;
    }
    currentFarmerUser = meRes.user;
    await loadWeatherBanner();
    await loadReminders();
  } catch (err) {
    console.warn("Authentication failed, redirecting to login:", err);
    window.location.href = "farmer-login.html";
  }
}

async function loadWeatherBanner() {
  try {
    const w = await AgriAPI.getAgriWeather();
    if (!w) return;

    const titleEl = document.getElementById("weather-banner-title");
    const descEl = document.getElementById("weather-banner-desc");

    if (w.rain_expected_24h) {
      if (titleEl) titleEl.innerHTML = `🌧️ मौसम अलर्ट: अगले 24 घंटों में ${w.rain_prob_today_pct}% बारिश की संभावना!`;
      if (descEl) descEl.innerHTML = `⚠️ खेत में जलभराव रोकने हेतु सिंचाई अनुस्मारक स्वतः स्थगित किए गए हैं। बारिश के बाद मिट्टी की नमी देखकर ही पानी दें।`;
    } else {
      if (titleEl) titleEl.innerHTML = `🌤️ मौसम अनुकूल: तापमान ${w.temperature_c}°C (मौसम शुष्क)`;
      if (descEl) descEl.innerHTML = `छिड़काव व सिंचाई हेतु मौसम उत्तम है। फसल की क्रांतिक अवस्था के अनुसार कार्य जारी रखें।`;
    }
  } catch (e) {
    console.error("Error loading weather banner:", e);
  }
}

async function loadReminders() {
  if (!currentFarmerUser) return;
  try {
    const res = await AgriAPI.getFarmerReminders(currentFarmerUser.id);
    if (res && res.reminders) {
      allReminders = res.reminders;
      updateCounters();
      renderReminders();
    }
  } catch (e) {
    console.error("Error loading reminders:", e);
    const grid = document.getElementById("reminders-grid");
    if (grid) {
      grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: red;">अनुस्मारक लोड करने में त्रुटि: ${e.message}</div>`;
    }
  }
}

function updateCounters() {
  let irrCount = 0;
  let fertCount = 0;
  let pestCount = 0;
  let weedCount = 0;
  let harvestCount = 0;
  let doneCount = 0;

  allReminders.forEach(r => {
    if (r.is_completed) {
      doneCount++;
    } else {
      const t = (r.reminder_type || "").toLowerCase();
      if (t.includes("irrigation") || t.includes("पानी") || t.includes("water")) irrCount++;
      else if (t.includes("fertilizer") || t.includes("nutrient") || t.includes("खाद") || t.includes("यूरिया")) fertCount++;
      else if (t.includes("inspection") || t.includes("pest") || t.includes("कीट") || t.includes("रोग")) pestCount++;
      else if (t.includes("weeding") || t.includes("निराई")) weedCount++;
      else if (t.includes("harvest") || t.includes("कटाई")) harvestCount++;
    }
  });

  const elIrr = document.getElementById("count-irrigation"); if (elIrr) elIrr.innerText = irrCount;
  const elFert = document.getElementById("count-fertilizer"); if (elFert) elFert.innerText = fertCount;
  const elPest = document.getElementById("count-pest"); if (elPest) elPest.innerText = pestCount;
  const elWeed = document.getElementById("count-weeding"); if (elWeed) elWeed.innerText = weedCount;
  const elHarv = document.getElementById("count-harvest"); if (elHarv) elHarv.innerText = harvestCount;
  const elDone = document.getElementById("count-completed"); if (elDone) elDone.innerText = doneCount;
}

function filterReminders(filterType, btn) {
  currentFilter = filterType;
  document.querySelectorAll(".filter-btn, .filter-chip").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  // Dynamic ambient category background shift
  document.body.classList.remove("cat-irrigation", "cat-fertilizer", "cat-pest", "cat-weeding", "cat-harvest");
  if (filterType !== "all" && filterType !== "completed") {
    document.body.classList.add(`cat-${filterType}`);
  }

  renderReminders();
}

function getUrgencyBadge(dueDateStr, isDone) {
  if (isDone) {
    return `<span class="badge-urgency badge-completed">✓ कार्य पूर्ण</span>`;
  }
  if (!dueDateStr) {
    return `<span class="badge-urgency badge-upcoming">📅 शीघ्र (Upcoming)</span>`;
  }
  
  const match = dueDateStr.match(/\d{4}-\d{2}-\d{2}/);
  if (match) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(match[0]);
    due.setHours(0, 0, 0, 0);
    const diffDays = Math.round((due - today) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return `<span class="badge-urgency badge-overdue">⚠️ अतिदेय (${Math.abs(diffDays)} दिन पूर्व)</span>`;
    } else if (diffDays === 0) {
      return `<span class="badge-urgency badge-today">🔥 आज ही देय (Due Today)</span>`;
    } else if (diffDays === 1) {
      return `<span class="badge-urgency badge-upcoming">⏳ कल देय (${dueDateStr})</span>`;
    } else {
      return `<span class="badge-urgency badge-upcoming">⏳ ${diffDays} दिन शेष (${dueDateStr})</span>`;
    }
  }
  
  return `<span class="badge-urgency badge-upcoming">📅 ${dueDateStr}</span>`;
}

function renderReminders() {
  const container = document.getElementById("reminders-grid");
  if (!container) return;
  container.innerHTML = "";

  let filtered = allReminders;
  if (currentFilter === "completed") {
    filtered = allReminders.filter(r => r.is_completed === 1);
  } else if (currentFilter === "irrigation") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || "").includes("irrigation") || (r.title || "").includes("सिंचाई")));
  } else if (currentFilter === "fertilizer") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || "").includes("fertilizer") || (r.reminder_type || "").includes("nutrient") || (r.title || "").includes("खाद")));
  } else if (currentFilter === "pest") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || "").includes("pest") || (r.reminder_type || "").includes("inspection") || (r.title || "").includes("कीट")));
  } else if (currentFilter === "weeding") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || "").includes("weeding")));
  } else if (currentFilter === "harvest") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || "").includes("harvest")));
  } else {
    filtered = [...allReminders].sort((a, b) => a.is_completed - b.is_completed);
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <span class="empty-state-icon">🌾</span>
        <h3 style="font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 6px;">इस श्रेणी में कोई अनुस्मारक नहीं है</h3>
        <p style="font-size: 13px; color: var(--text-muted); max-width: 420px; margin: 0 auto 16px;">
          आप ऊपर दिए गए 'बोलकर या लिखकर रिमाइंडर जोड़ें' बार या '+ नया अनुस्मारक' बटन से नया कृषि कार्य जोड़ सकते हैं।
        </p>
      </div>
    `;
    return;
  }

  filtered.forEach(r => {
    const card = document.createElement("div");
    const t = (r.reminder_type || "general").toLowerCase();
    const isDone = r.is_completed === 1;

    let catClass = "rem-general";
    let icon = "📋";
    let catLabel = "सामान्य कार्य";

    if (t.includes("irrigation") || t.includes("सिंचाई") || t.includes("water")) {
      catClass = "rem-irrigation"; icon = "💧"; catLabel = "सिंचाई प्रबंधन";
    } else if (t.includes("fertilizer") || t.includes("nutrient") || t.includes("खाद") || t.includes("यूरिया")) {
      catClass = "rem-fertilizer"; icon = "🌱"; catLabel = "उर्वरक / खाद";
    } else if (t.includes("pest") || t.includes("inspection") || t.includes("कीट") || t.includes("रोग") || t.includes("spray") || t.includes("छिड़काव")) {
      catClass = "rem-pest"; icon = "🛡️"; catLabel = "कीट / रोग नियंत्रण";
    } else if (t.includes("weeding") || t.includes("निराई")) {
      catClass = "rem-weeding"; icon = "🌿"; catLabel = "निराई-गुड़ाई";
    } else if (t.includes("harvest") || t.includes("कटाई")) {
      catClass = "rem-harvest"; icon = "🌾"; catLabel = "कटाई व कटाई-उपरांत";
    }

    card.className = `rem-card ${catClass} ${isDone ? 'rem-done' : ''}`;

    const localCreated = AgriAPI.formatLocalDateTime(r.created_at);
    const urgencyHtml = getUrgencyBadge(r.due_date, isDone);
    const isHighPriority = (r.priority || "").toLowerCase() === "high";

    card.innerHTML = `
      <div class="rem-card-header">
        <div style="display: flex; align-items: flex-start; gap: 12px;">
          <div class="rem-type-icon">${icon}</div>
          <div>
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 2px;">
              <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">${catLabel}</span>
              ${isHighPriority ? '<span style="font-size: 10.5px; font-weight: 800; color: #DC2626; background: #FEE2E2; padding: 1px 6px; border-radius: 4px;">🔴 उच्च प्राथमिकता</span>' : ''}
            </div>
            <h3 style="font-size: 15px; font-weight: 700; color: var(--text); ${isDone ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">${r.title}</h3>
            <span style="font-size: 11px; color: var(--text-muted);">बनाया गया: ${localCreated}</span>
          </div>
        </div>
        <div>${urgencyHtml}</div>
      </div>
      <p style="font-size: 12.8px; color: var(--text-muted); margin: 8px 0 12px 0; line-height: 1.55; padding-left: 52px;">
        ${r.description || 'कोई अतिरिक्त विवरण दर्ज नहीं है।'}
      </p>
      <div class="rem-actions">
        <button class="btn ${isDone ? 'btn-secondary' : 'btn-primary'}" style="font-size: 11.5px; padding: 5px 12px; font-weight: 700;" onclick="handleToggleReminder('${r.id}')">
          ${isDone ? '↺ पुनः सक्रिय करें' : '✓ कार्य संपन्न करें'}
        </button>
        <button class="btn btn-outline" style="font-size: 11.5px; padding: 5px 10px; color: #DC2626; border-color: rgba(220,38,38,0.25);" onclick="handleDeleteReminder('${r.id}')">
          🗑️ हटाएं
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

async function handleToggleReminder(reminderId) {
  try {
    await AgriAPI.toggleReminder(reminderId);
    await loadReminders();
  } catch (e) {
    alert("स्थिति बदलने में त्रुटि: " + e.message);
  }
}

async function handleDeleteReminder(reminderId) {
  if (!confirm("क्या आप यह अनुस्मारक हटाना चाहते हैं?")) return;
  try {
    await AgriAPI.deleteReminder(reminderId);
    await loadReminders();
  } catch (e) {
    alert("हटाने में त्रुटि: " + e.message);
  }
}

function openAddModal() {
  const m = document.getElementById("add-modal");
  if (m) m.classList.add("active");
}

function closeAddModal() {
  const m = document.getElementById("add-modal");
  if (m) m.classList.remove("active");
}

async function handleSaveCustomReminder() {
  const title = document.getElementById("m-title").value.trim();
  const type = document.getElementById("m-type").value;
  const due = document.getElementById("m-due").value.trim() || "शीघ्र";
  const desc = document.getElementById("m-desc").value.trim();

  if (!title) {
    alert("कृपया कार्य का नाम लिखें।");
    return;
  }

  try {
    await AgriAPI.createCustomReminder({
      title: title,
      description: desc,
      due_date: due,
      reminder_type: type,
      priority: "high"
    });
    closeAddModal();
    document.getElementById("m-title").value = "";
    document.getElementById("m-desc").value = "";
    await loadReminders();
  } catch (e) {
    alert("अनुस्मारक जोड़ने में त्रुटि: " + e.message);
  }
}

async function handleQuickAddNLP() {
  const input = document.getElementById("nl-input");
  const text = input.value.trim();
  if (!text) return;

  try {
    const fid = currentFarmerUser ? currentFarmerUser.id : null;
    const res = await AgriAPI.createNaturalReminder(text, fid);
    alert(`स्मार्ट रिमाइंडर बन गया: "${res.reminder.title}" (${res.reminder.due_date})`);
    input.value = "";
    await loadReminders();
  } catch (e) {
    alert("त्रुटि: " + e.message);
  }
}
