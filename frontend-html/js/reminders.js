/**
 * AgriGo — Positivus AI Crop Schedule & Reminders Controller
 * Interacts with DeepSeek AI / Gemini / ICAR Agronomy backend
 */

let allReminders = [];
let currentFilter = "all";
let currentFarmerUser = null;
let currentAcreage = 2.5;
let currentCropName = "गेहूं (Wheat)";
let allStagesExpanded = false;

function hideLoadingOverlay() {
  const overlay = document.getElementById("pos-loading-overlay") || document.getElementById("loading-overlay");
  if (overlay) {
    overlay.style.display = "none";
    overlay.classList.remove("active");
    overlay.classList.add("hidden");
  }
}

function showLoadingOverlay(msg) {
  const overlay = document.getElementById("pos-loading-overlay") || document.getElementById("loading-overlay");
  const statusText = document.getElementById("loading-status-text");
  if (statusText && msg) statusText.innerText = msg;
  if (overlay) {
    overlay.style.display = "flex";
    overlay.classList.add("active");
    overlay.classList.remove("hidden");
  }
}

async function initRemindersPage() {
  hideLoadingOverlay();
  initFormDefaults();
  await checkFarmerAuth();
  hideLoadingOverlay();
}

// Immediate dismissal in case CSS was cached
hideLoadingOverlay();

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initRemindersPage);
} else {
  initRemindersPage();
}

window.addEventListener("pageshow", async () => {
  hideLoadingOverlay();
  await checkFarmerAuth();
});

function initFormDefaults() {
  // Set default sowing date to today
  const dateInput = document.getElementById("schedule-sowing-date");
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().split("T")[0];
    dateInput.value = today;
  }
}

async function checkFarmerAuth() {
  try {
    const meRes = await AgriAPI.getMe().catch(() => null);
    if (meRes && meRes.authenticated && meRes.user) {
      currentFarmerUser = meRes.user;
      if (currentFarmerUser.farm_area) {
        currentAcreage = parseFloat(currentFarmerUser.farm_area) || 2.5;
        const acreInput = document.getElementById("schedule-acreage");
        if (acreInput) acreInput.value = currentAcreage;
      }
      if (currentFarmerUser.primary_crop) {
        const cropSelect = document.getElementById("schedule-crop-name");
        if (cropSelect) {
          for (let i = 0; i < cropSelect.options.length; i++) {
            if (cropSelect.options[i].value.includes(currentFarmerUser.primary_crop)) {
              cropSelect.selectedIndex = i;
              currentCropName = cropSelect.options[i].value;
              break;
            }
          }
        }
      }
    } else {
      // Guest / Beginner Farmer Mode — NEVER redirect or lock the user out!
      currentFarmerUser = {
        id: "farmer-guest",
        name: "किसान साथी",
        farm_area: 2.5,
        primary_crop: "गेहूं (Wheat)"
      };
    }
  } catch (err) {
    console.warn("Auth check error, falling back to guest mode:", err);
    currentFarmerUser = {
      id: "farmer-guest",
      name: "किसान साथी",
      farm_area: 2.5,
      primary_crop: "गेहूं (Wheat)"
    };
  }

  // Always load reminders immediately!
  await loadReminders();
}

async function loadReminders() {
  if (!currentFarmerUser) return;
  try {
    let res = await AgriAPI.getFarmerReminders(currentFarmerUser.id).catch(() => null);
    if (!res || !res.reminders || res.reminders.length === 0) {
      // First visit: automatically auto-generate initial ICAR baseline schedule for active crop
      const today = new Date().toISOString().split("T")[0];
      const genRes = await AgriAPI.generateCropSchedule(currentCropName, today, currentAcreage, currentFarmerUser.id).catch(() => null);
      if (genRes && genRes.schedule && genRes.schedule.created_reminders) {
        allReminders = genRes.schedule.created_reminders;
      } else {
        res = await AgriAPI.getFarmerReminders(currentFarmerUser.id).catch(() => null);
        if (res && res.reminders) {
          allReminders = res.reminders;
        }
      }
    } else {
      allReminders = res.reminders;
    }
  } catch (e) {
    console.warn("Notice loading reminders:", e);
  } finally {
    updateMetricsAndHero();
    renderProcessStages();
    renderAllRemindersList();
    if (window.AgriI18n && window.AgriI18n.applyTranslation) {
      window.AgriI18n.applyTranslation();
    }
  }
}

// Seamless English/Hindi language change listener
window.addEventListener("agrigo:langchange", () => {
  updateMetricsAndHero();
  renderProcessStages();
  renderAllRemindersList();
  if (window.AgriI18n && window.AgriI18n.applyTranslation) {
    window.AgriI18n.applyTranslation();
  }
});

/**
 * Updates Top Hero Badge, Counters and Positivus Summary Cards
 */
function updateMetricsAndHero() {
  let irrCount = 0;
  let fertCount = 0;
  let pestCount = 0;
  let doneCount = 0;
  let nextIrrigationDate = null;
  let totalDap = 0;
  let totalUrea = 0;
  let totalMop = 0;

  const todayStr = new Date().toISOString().split("T")[0];

  // Comprehensive 30+ Crop Detection
  const detectedCropsInReminders = new Set();
  const cropMappings = [
    { name: "गेहूं (Wheat)", keys: ["गेहूं", "wheat"] },
    { name: "सरसों (Mustard)", keys: ["सरसों", "mustard", "राई"] },
    { name: "धान (Paddy / Rice)", keys: ["धान", "paddy", "rice", "चावल"] },
    { name: "चना (Gram / Chickpea)", keys: ["चना", "gram", "chickpea"] },
    { name: "मक्का (Maize)", keys: ["मक्का", "maize", "corn"] },
    { name: "कपास (Cotton)", keys: ["कपास", "cotton"] },
    { name: "आलू (Potato)", keys: ["आलू", "potato"] },
    { name: "टमाटर (Tomato)", keys: ["टमाटर", "tomato"] },
    { name: "प्याज (Onion)", keys: ["प्याज", "onion"] },
    { name: "लहसुन (Garlic)", keys: ["लहसुन", "garlic"] },
    { name: "मिर्च (Chilli)", keys: ["मिर्च", "chilli", "chili"] },
    { name: "बैंगन (Brinjal)", keys: ["बैंगन", "brinjal", "eggplant"] },
    { name: "फूलगोभी (Cauliflower)", keys: ["फूलगोभी", "cauliflower"] },
    { name: "पत्तागोभी (Cabbage)", keys: ["पत्तागोभी", "cabbage"] },
    { name: "भिंडी (Okra)", keys: ["भिंडी", "okra", "bhindi"] },
    { name: "सोयाबीन (Soybean)", keys: ["सोयाबीन", "soybean"] },
    { name: "गन्ना (Sugarcane)", keys: ["गन्ना", "sugarcane"] },
    { name: "बाजरा (Pearl Millet)", keys: ["बाजरा", "bajra", "pearl millet"] },
    { name: "ज्वार (Sorghum)", keys: ["ज्वार", "jowar", "sorghum"] },
    { name: "जौ (Barley)", keys: ["जौ", "jau", "barley"] },
    { name: "अरहर (Pigeon Pea / Arhar)", keys: ["अरहर", "arhar", "tur", "तुअर"] },
    { name: "मूंग (Green Gram)", keys: ["मूंग", "moong", "green gram"] },
    { name: "उड़द (Black Gram)", keys: ["उड़द", "urad", "black gram"] },
    { name: "मटर (Green Pea)", keys: ["मटर", "pea", "matar"] },
    { name: "मसूर (Lentil)", keys: ["मसूर", "masoor", "lentil"] },
    { name: "मूंगफली (Groundnut)", keys: ["मूंगफली", "groundnut", "peanut"] },
    { name: "सूरजमुखी (Sunflower)", keys: ["सूरजमुखी", "sunflower"] },
    { name: "अदरक (Ginger)", keys: ["अदरक", "ginger"] },
    { name: "हल्दी (Turmeric)", keys: ["हल्दी", "turmeric"] },
    { name: "जीरा (Cumin / Jeera)", keys: ["जीरा", "jeera", "cumin"] },
    { name: "धनिया (Coriander)", keys: ["धनिया", "dhaniya", "coriander"] },
    { name: "तरबूज (Watermelon)", keys: ["तरबूज", "watermelon"] }
  ];

  allReminders.forEach(r => {
    const isCompleted = r.is_completed === 1;
    const t = (r.reminder_type || r.category || "").toLowerCase();
    const title = (r.title || "").toLowerCase();

    for (const cm of cropMappings) {
      if (cm.keys.some(k => title.includes(k))) {
        detectedCropsInReminders.add(cm.name);
        break;
      }
    }

    if (isCompleted) {
      doneCount++;
    } else {
      if (t.includes("irrigation") || t.includes("पानी") || title.includes("सिंचाई")) {
        irrCount++;
        if (r.due_date && (!nextIrrigationDate || r.due_date < nextIrrigationDate)) {
          nextIrrigationDate = r.due_date;
        }
      } else if (t.includes("fertilizer") || t.includes("खाद") || title.includes("यूरिया") || title.includes("dap") || title.includes("उर्वरक")) {
        fertCount++;
      } else if (t.includes("pest") || t.includes("कीट") || t.includes("रोग") || t.includes("spray") || title.includes("छिड़काव")) {
        pestCount++;
      }
    }

    if (r.acreage) {
      currentAcreage = parseFloat(r.acreage);
    }
  });

  if (detectedCropsInReminders.size > 0) {
    currentCropName = Array.from(detectedCropsInReminders).join(" + ");
  }

  if (allReminders.length === 0) {
    irrCount = 5;
    fertCount = 3;
    pestCount = 3;
  }

  // Update Hero Stats
  const heroIrr = document.getElementById("hero-stat-irr");
  const heroFert = document.getElementById("hero-stat-fert");
  const heroPest = document.getElementById("hero-stat-pest");
  if (heroIrr) heroIrr.innerText = irrCount;
  if (heroFert) heroFert.innerText = fertCount;
  if (heroPest) heroPest.innerText = pestCount;

  // Update Active Crop Badge
  const cropBadge = document.getElementById("active-crop-badge");
  if (cropBadge) {
    cropBadge.innerText = `सक्रिय फसल: ${currentCropName} (${currentAcreage} एकड़)`;
  }

  // Update Summary Service Cards
  const statIrrCount = document.getElementById("stat-irr-count");
  if (statIrrCount) statIrrCount.innerText = irrCount;

  const statNextIrr = document.getElementById("stat-next-irr");
  if (statNextIrr) {
    if (nextIrrigationDate) {
      statNextIrr.innerText = `💧 अगली सिंचाई: ${formatDueDateLabel(nextIrrigationDate)}`;
    } else {
      statNextIrr.innerText = `💧 प्रथम सिंचाई: बुवाई के 21 दिन बाद (CRI स्टेज)`;
    }
  }

  // Dynamic Crop-Specific Fertilizer Calculations for all 30+ Crops
  const statFertBreakdown = document.getElementById("stat-fert-breakdown");
  if (statFertBreakdown) {
    const cName = currentCropName.toLowerCase();
    if (cName.includes("सरसों") || cName.includes("mustard")) {
      totalDap = Math.round(30 * currentAcreage);
      totalUrea = Math.round(35 * currentAcreage);
      totalMop = Math.round(15 * currentAcreage);
      const totalSulf = Math.round(10 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>सरसों (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg • पोटाश: ${totalMop} kg • सल्फर/SSP: ${totalSulf} kg (ICAR: तेल प्रतिशत व दाना चमक हेतु)।`;
    } else if (cName.includes("चना") || cName.includes("मूंग") || cName.includes("उड़द") || cName.includes("मटर") || cName.includes("मसूर") || cName.includes("अरहर") || cName.includes("gram") || cName.includes("pulse")) {
      totalDap = Math.round(40 * currentAcreage);
      totalMop = Math.round(15 * currentAcreage);
      const totalSulf = Math.round(8 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>दलहनी फसल (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • पोटाश: ${totalMop} kg • सल्फर: ${totalSulf} kg (दलहन में यूरिया टॉप-ड्रेसिंग न दें, 19:19:19 स्प्रे करें)।`;
    } else if (cName.includes("धान") || cName.includes("rice") || cName.includes("paddy")) {
      totalDap = Math.round(40 * currentAcreage);
      totalUrea = Math.round(65 * currentAcreage);
      totalMop = Math.round(25 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>धान (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg (2 खुराकों में) • पोटाश: ${totalMop} kg • जिंक: ${Math.round(10 * currentAcreage)} kg।`;
    } else if (cName.includes("कपास") || cName.includes("cotton")) {
      totalDap = Math.round(50 * currentAcreage);
      totalUrea = Math.round(70 * currentAcreage);
      totalMop = Math.round(30 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>कपास (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg • पोटाश: ${totalMop} kg • मैग्नीशियम सल्फेट: ${Math.round(10 * currentAcreage)} kg।`;
    } else if (cName.includes("आलू") || cName.includes("potato")) {
      totalDap = Math.round(60 * currentAcreage);
      totalUrea = Math.round(75 * currentAcreage);
      totalMop = Math.round(40 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>आलू (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg • पोटाश: ${totalMop} kg (कंद का आकार व छिलका सुदृढ़ करने हेतु)।`;
    } else if (cName.includes("टमाटर") || cName.includes("मिर्च") || cName.includes("बैंगन") || cName.includes("tomato") || cName.includes("chilli")) {
      totalDap = Math.round(50 * currentAcreage);
      totalUrea = Math.round(60 * currentAcreage);
      totalMop = Math.round(30 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>सब्जी फसल (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg • पोटाश: ${totalMop} kg + बोरॉन स्प्रे (फल फटने से बचाव)।`;
    } else if (cName.includes("प्याज") || cName.includes("लहसुन") || cName.includes("onion") || cName.includes("garlic")) {
      totalDap = Math.round(45 * currentAcreage);
      totalUrea = Math.round(50 * currentAcreage);
      totalMop = Math.round(25 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>कंद फसल (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg • पोटाश: ${totalMop} kg • सल्फर: ${Math.round(12 * currentAcreage)} kg (तीखापन व भंडारण हेतु)।`;
    } else if (cName.includes("गन्ना") || cName.includes("sugarcane")) {
      totalDap = Math.round(60 * currentAcreage);
      totalUrea = Math.round(110 * currentAcreage);
      totalMop = Math.round(40 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>गन्ना (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg (3 खुराकों में) • पोटाश: ${totalMop} kg।`;
    } else {
      totalDap = Math.round(55 * currentAcreage);
      totalUrea = Math.round(90 * currentAcreage);
      totalMop = Math.round(25 * currentAcreage);
      statFertBreakdown.innerHTML = `<strong>${currentCropName.split(" ")[0]} (${currentAcreage} एकड़):</strong> DAP: ${totalDap} kg • यूरिया: ${totalUrea} kg (विभाजित खुराक) • पोटाश: ${totalMop} kg • जिंक: ${Math.round(10 * currentAcreage)} kg।`;
    }
  }

  const statFertAcreageNote = document.getElementById("stat-fert-acreage-note");
  if (statFertAcreageNote) {
    statFertAcreageNote.innerText = `🌾 कुल रकबा: ${currentAcreage} एकड़ (ICAR वैज्ञानिक अनुशंसा)`;
  }

  const statPestCount = document.getElementById("stat-pest-count");
  if (statPestCount) statPestCount.innerText = pestCount;

  // Filter Pills Counts
  const pAll = document.getElementById("pill-all-count"); if (pAll) pAll.innerText = allReminders.length;
  const pIrr = document.getElementById("pill-irr-count"); if (pIrr) pIrr.innerText = irrCount;
  const pFert = document.getElementById("pill-fert-count"); if (pFert) pFert.innerText = fertCount;
  const pPest = document.getElementById("pill-pest-count"); if (pPest) pPest.innerText = pestCount;
  const pDone = document.getElementById("pill-done-count"); if (pDone) pDone.innerText = doneCount;
}

/**
 * Standard 5 Phenological Stages for Positivus Working Process Accordion
 */
const DEFAULT_PHENOLOGICAL_STAGES = [
  {
    num: "01",
    title: "बुवाई व आधार खाद चरण (Basal & Sowing Stage)",
    days: "बुवाई के 0-15 दिन",
    keywords: ["01", "basal", "sowing", "अंकुरण", "बुवाई", "रोपाई", "स्थापना", "शुरुआती"]
  },
  {
    num: "02",
    title: "वानस्पतिक व कल्ले फूटने का चरण (Vegetative & Tillering Stage)",
    days: "बुवाई के 16-45 दिन",
    keywords: ["02", "tillering", "vegetative", "कल्ले", "वानस्पतिक", "निराई", "रोजेट", "rosette", "घुटने", "knee", "बढ़वार", "शाखाएं", "cri", "चौपड़ा"]
  },
  {
    num: "03",
    title: "गाभा व फूल आने का क्रांतिक चरण (Booting & Flowering Stage)",
    days: "बुवाई के 46-75 दिन",
    keywords: ["03", "booting", "flowering", "गाभा", "फूल", "बालियां", "मंजर", "silking", "कली", "गांठ", "jointing", "टिंडे", "घंटी"]
  },
  {
    num: "04",
    title: "दाना भराव व दुग्ध अवस्था (Grain Filling & Milking Stage)",
    days: "बुवाई के 76-105 दिन",
    keywords: ["04", "milking", "dough", "भराव", "दुग्ध", "दाना", "कंद", "tuber", "फल विकास", "siliquae", "फली", "टिंडा विकास"]
  },
  {
    num: "05",
    title: "परिपक्वता व कटाई चरण (Maturity & Harvesting Stage)",
    days: "बुवाई के 106-140 दिन",
    keywords: ["05", "harvest", "maturity", "कटाई", "परिपक्व", "खुदाई", "picking", "तोड़ाई", "चुनाई"]
  }
];

function renderProcessStages() {
  const container = document.getElementById("process-stages-container");
  if (!container) return;

  if (allReminders.length === 0) {
    return;
  }

  container.innerHTML = "";

  DEFAULT_PHENOLOGICAL_STAGES.forEach((stageDef, index) => {
    // Find all reminders matching this stage
    const matchingTasks = allReminders.filter(r => {
      const stageName = (r.stage_name || "").toLowerCase();
      const title = (r.title || "").toLowerCase();
      const desc = (r.description || "").toLowerCase();

      // 1. Direct stage number match (e.g. "01 - ...")
      if (stageName.startsWith(stageDef.num) || stageName.includes(` ${stageDef.num}`) || stageName.includes(`-${stageDef.num}`)) {
        return true;
      }

      // 2. Keyword match
      return stageDef.keywords.some(kw => stageName.includes(kw) || title.includes(kw) || desc.includes(kw));
    });

    const isFirstActive = (index === 0 && !allStagesExpanded) || allStagesExpanded;
    const taskCount = matchingTasks.length;

    const item = document.createElement("div");
    item.className = `pos-process-item ${isFirstActive ? 'active' : ''}`;
    item.id = `stage-item-${stageDef.num}`;

    let tasksHtml = "";
    if (taskCount === 0) {
      tasksHtml = `
        <div style="font-size:13px; color:#6B7280; padding:12px; background:#FFF; border-radius:12px; border:1.5px dashed #D1D5DB; text-align:center;">
          इस चरण में कोई लंबित कार्य नहीं है।
        </div>
      `;
    } else {
      tasksHtml = `<div class="pos-tasks-grid">`;
      matchingTasks.forEach(t => {
        tasksHtml += buildTaskCardHtml(t);
      });
      tasksHtml += `</div>`;
    }

    item.innerHTML = `
      <div class="pos-process-header" onclick="toggleProcessStage('${stageDef.num}')">
        <div class="pos-process-left">
          <span class="pos-process-num">${stageDef.num}</span>
          <div>
            <h3 class="pos-process-title">${stageDef.title}</h3>
            <div style="display:flex; align-items:center; gap:8px; margin-top:4px; flex-wrap:wrap;">
              <span class="pos-pill" style="font-size:11px; padding:2px 8px; border:1px solid var(--pos-border);">${stageDef.days}</span>
              <span style="font-size:12px; font-weight:800; color:var(--pos-dark);">${taskCount} कार्य संलग्न</span>
            </div>
          </div>
        </div>
        <div class="pos-process-toggle">+</div>
      </div>
      <div class="pos-process-body" id="stage-body-${stageDef.num}" style="${isFirstActive ? 'display:block;' : 'display:none;'}">
        <div style="font-size:12.5px; font-weight:700; color:var(--pos-dark); margin-bottom:10px;">
          📋 इस चरण के अंतर्गत आने वाले वैज्ञानिक कार्य:
        </div>
        ${tasksHtml}
      </div>
    `;

    container.appendChild(item);
  });
}

/**
 * Toggle individual stage accordion
 */
function toggleProcessStage(stageNum) {
  const item = document.getElementById(`stage-item-${stageNum}`);
  const body = document.getElementById(`stage-body-${stageNum}`);
  if (!item || !body) return;

  if (item.classList.contains("active")) {
    item.classList.remove("active");
    body.style.display = "none";
  } else {
    item.classList.add("active");
    body.style.display = "block";
  }
}

/**
 * Expand or Collapse all process stages
 */
function expandAllProcessStages() {
  allStagesExpanded = !allStagesExpanded;
  DEFAULT_PHENOLOGICAL_STAGES.forEach(s => {
    const item = document.getElementById(`stage-item-${s.num}`);
    const body = document.getElementById(`stage-body-${s.num}`);
    if (item && body) {
      if (allStagesExpanded) {
        item.classList.add("active");
        body.style.display = "block";
      } else {
        item.classList.remove("active");
        body.style.display = "none";
      }
    }
  });
}

/**
 * Build HTML for a single task card inside a stage or list
 */
function buildTaskCardHtml(r) {
  const isDone = r.is_completed === 1;
  const t = (r.reminder_type || r.category || "general").toLowerCase();

  let tagClass = "tag-irrigation";
  let icon = "💧";
  let tagLabel = "सिंचाई";

  if (t.includes("fertilizer") || t.includes("खाद") || (r.title || "").includes("यूरिया") || (r.title || "").includes("dap")) {
    tagClass = "tag-fertilizer";
    icon = "🌱";
    tagLabel = "खाद व पोषण";
  } else if (t.includes("pest") || t.includes("कीट") || t.includes("रोग") || (r.title || "").includes("छिड़काव")) {
    tagClass = "tag-pest";
    icon = "🛡️";
    tagLabel = "पादप सुरक्षा";
  }

  const urgencyBadge = getPositivusUrgencyBadge(r.due_date, isDone);
  const dosageNote = r.dosage_info ? `<div style="font-size:12.5px; font-weight:800; color:#78350F; background:#FEF3C7; border:1.5px solid #D97706; border-radius:8px; padding:6px 10px; margin:8px 0;">⚖️ खुराक: ${r.dosage_info}</div>` : '';

  return `
    <div class="pos-task-card ${isDone ? 'task-done' : ''}">
      <div>
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px; margin-bottom:8px;">
          <span class="pos-task-tag ${tagClass}">${icon} ${tagLabel}</span>
          ${urgencyBadge}
        </div>
        <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin:4px 0 6px 0; ${isDone ? 'text-decoration:line-through; color:#6B7280;' : ''}">
          ${r.title}
        </h4>
        <p style="font-size:13.5px; color:#1F2937; line-height:1.55; margin:0; font-weight:500;">
          ${r.description || 'विशिष्ट निर्देश उपलब्ध नहीं हैं।'}
        </p>
        ${dosageNote}
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; padding-top:10px; border-top:1.5px solid #E2E8F0;">
        <span style="font-size:12px; font-weight:800; color:#0F172A;">देय: ${r.due_date || 'शीघ्र'}</span>
        <div style="display:flex; gap:6px;">
          <button type="button" class="pos-btn ${isDone ? 'pos-btn-outline' : 'pos-btn-lime'}" style="padding:5px 12px; font-size:12px; border-radius:8px; font-weight:800;" onclick="handleToggleReminder('${r.id}')" aria-label="${isDone ? 'कार्य पुनः सक्रिय करें' : 'कार्य पूर्ण चिह्नित करें'}">
            ${isDone ? '↺ सक्रिय' : '✓ पूर्ण'}
          </button>
          <button type="button" class="pos-btn pos-btn-outline" style="padding:5px 10px; font-size:12px; border-radius:8px; color:#DC2626; border-color:#DC2626;" onclick="handleDeleteReminder('${r.id}')" aria-label="कार्य हटाएं" title="हटाएं (Delete)">
            🗑️
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Urgency badge generator
 */
function getPositivusUrgencyBadge(dueDateStr, isDone) {
  if (isDone) {
    return `<span class="pos-pill" style="background:#DCFCE7; color:#14532D; border:1.5px solid #16A34A; font-size:11.5px; font-weight:800; padding:3px 8px;">✓ पूर्ण</span>`;
  }
  if (!dueDateStr) {
    return `<span class="pos-pill" style="background:#E0F2FE; color:#034E7B; border:1.5px solid #0284C7; font-size:11.5px; font-weight:800; padding:3px 8px;">📅 शीघ्र</span>`;
  }

  const match = dueDateStr.match(/\d{4}-\d{2}-\d{2}/);
  if (match) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(match[0]);
    due.setHours(0, 0, 0, 0);
    const diffDays = Math.round((due - today) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `<span class="pos-pill" style="background:#FEE2E2; color:#991B1B; border:1.5px solid #DC2626; font-size:11.5px; font-weight:800; padding:3px 8px;">⚠️ ${Math.abs(diffDays)} दिन पूर्व</span>`;
    } else if (diffDays === 0) {
      return `<span class="pos-pill" style="background:#FEF08A; color:#713F12; border:1.5px solid #CA8A04; font-size:11.5px; font-weight:800; padding:3px 8px;">🔥 आज देय</span>`;
    } else if (diffDays === 1) {
      return `<span class="pos-pill" style="background:#E0F2FE; color:#034E7B; border:1.5px solid #0284C7; font-size:11.5px; font-weight:800; padding:3px 8px;">⏳ कल देय</span>`;
    } else {
      return `<span class="pos-pill" style="background:#E0F2FE; color:#034E7B; border:1.5px solid #0284C7; font-size:11.5px; font-weight:800; padding:3px 8px;">⏳ ${diffDays} दिन शेष</span>`;
    }
  }

  return `<span class="pos-pill" style="background:#F3F4F6; color:#0F172A; border:1.5px solid #0F172A; font-size:11.5px; font-weight:800; padding:3px 8px;">📅 ${dueDateStr}</span>`;
}

function formatDueDateLabel(dueDateStr) {
  const match = dueDateStr.match(/\d{4}-\d{2}-\d{2}/);
  if (!match) return dueDateStr;
  const parts = match[0].split("-");
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

/**
 * Render All Reminders Grid with Filter Pills
 */
function renderAllRemindersList() {
  const container = document.getElementById("reminders-grid");
  if (!container) return;
  container.innerHTML = "";

  let filtered = allReminders;
  if (currentFilter === "completed") {
    filtered = allReminders.filter(r => r.is_completed === 1);
  } else if (currentFilter === "irrigation") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || r.category || "").includes("irrigation") || (r.title || "").includes("सिंचाई")));
  } else if (currentFilter === "fertilizer") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || r.category || "").includes("fertilizer") || (r.title || "").includes("खाद") || (r.title || "").includes("यूरिया")));
  } else if (currentFilter === "pesticide") {
    filtered = allReminders.filter(r => !r.is_completed && ((r.reminder_type || r.category || "").includes("pest") || (r.title || "").includes("कीट") || (r.title || "").includes("छिड़काव")));
  } else {
    // 'all' filter: sort uncompleted first
    filtered = [...allReminders].sort((a, b) => a.is_completed - b.is_completed);
  }

  if (filtered.length === 0) {
    const totalDap = Math.round(50 * currentAcreage);
    const totalMop = Math.round(25 * currentAcreage);
    const sampleReminders = [
      {
        id: "sample-1",
        title: `${currentCropName.split(" ")[0]}: आधार खाद अनुप्रयोग (Basal Fertilizer)`,
        description: `बुवाई के समय खेत में अनुशंसित DAP, पोटाश व जिंक की पूरी मात्रा डालें।`,
        due_date: "आज ही देय",
        reminder_type: "fertilizer",
        dosage_info: `DAP: ${totalDap} kg • पोटाश: ${totalMop} kg`,
        is_completed: 0
      },
      {
        id: "sample-2",
        title: `${currentCropName.split(" ")[0]}: पलेवा व बुवाई पूर्व सिंचाई`,
        description: `मिट्टी में पर्याप्त ओट आने पर बुवाई करें ताकि 100% अंकुरण हो।`,
        due_date: "बुवाई समय",
        reminder_type: "irrigation",
        is_completed: 0
      },
      {
        id: "sample-3",
        title: `${currentCropName.split(" ")[0]}: कल्ले फूटने पर प्रथम सिंचाई (CRI)`,
        description: `फसल की सबसे क्रांतिक अवस्था, पानी की कमी न होने दें।`,
        due_date: "21 दिन बाद",
        reminder_type: "irrigation",
        is_completed: 0
      },
      {
        id: "sample-4",
        title: `${currentCropName.split(" ")[0]}: यूरिया प्रथम टॉप-ड्रेसिंग`,
        description: `प्रथम सिंचाई उपरांत खेत में यूरिया का भुरकाव करें।`,
        due_date: "24 दिन बाद",
        reminder_type: "fertilizer",
        dosage_info: `यूरिया: ${Math.round(45 * currentAcreage)} kg`,
        is_completed: 0
      },
      {
        id: "sample-5",
        title: `${currentCropName.split(" ")[0]}: कीट व फफूंद सुरक्षा (IPM)`,
        description: `पत्तियों पर माहू या रतुआ रोग के लक्षणों का नियमित निरीक्षण करें।`,
        due_date: "40 दिन बाद",
        reminder_type: "pest",
        is_completed: 0
      }
    ];
    sampleReminders.forEach(r => {
      const cardEl = document.createElement("div");
      cardEl.innerHTML = buildTaskCardHtml(r);
      container.appendChild(cardEl.firstElementChild);
    });
    return;
  }

  filtered.forEach(r => {
    const cardEl = document.createElement("div");
    cardEl.innerHTML = buildTaskCardHtml(r);
    container.appendChild(cardEl.firstElementChild);
  });
}

function filterPositivusReminders(filterType, btn) {
  currentFilter = filterType;
  document.querySelectorAll(".pos-filter-pill").forEach(p => p.classList.remove("active"));
  if (btn) btn.classList.add("active");
  renderAllRemindersList();
}

/**
 * Handle Auto Generate Crop Schedule submission
 */
async function handleGenerateSchedule(e) {
  e.preventDefault();

  const cropSelect = document.getElementById("schedule-crop-name");
  let cropVal = cropSelect ? cropSelect.value : "";
  if (cropVal === "__custom__") {
    const customCropInput = document.getElementById("schedule-custom-crop");
    cropVal = customCropInput ? customCropInput.value.trim() : "";
  }
  if (!cropVal) {
    alert("कृपया फसल का नाम चुनें या लिखें।");
    return;
  }

  const sowingDateInput = document.getElementById("schedule-sowing-date");
  const sowingDateVal = sowingDateInput ? sowingDateInput.value : "";
  if (!sowingDateVal) {
    alert("कृपया बुवाई या रोपाई की तारीख चुनें।");
    return;
  }

  const acreageInput = document.getElementById("schedule-acreage");
  const acreageVal = acreageInput ? parseFloat(acreageInput.value) : 1.0;
  if (!acreageVal || acreageVal <= 0) {
    alert("कृपया मान्य एकड़ दर्ज करें।");
    return;
  }

  currentCropName = cropVal;
  currentAcreage = acreageVal;

  showLoadingOverlay(`OpenAI व ICAR द्वारा ${cropVal} (${acreageVal} एकड़) हेतु संपूर्ण समय-सारणी तैयार की जा रही है...`);

  try {
    const farmerId = currentFarmerUser ? currentFarmerUser.id : null;
    const res = await AgriAPI.generateCropSchedule(cropVal, sowingDateVal, acreageVal, farmerId);
    
    hideLoadingOverlay();

    alert(`🎉 बधाई हो! ${cropVal} के लिए ${acreageVal} एकड़ की संपूर्ण समय-सारणी (${res?.schedule?.total_tasks_created || 15} कार्य) सफलतापूर्वक तैयार कर ली गई है!`);
    await loadReminders();

    // Scroll smoothly to the summary section
    const summarySection = document.querySelector(".pos-summary-grid");
    if (summarySection) {
      summarySection.scrollIntoView({ behavior: "smooth" });
    }
  } catch (err) {
    hideLoadingOverlay();
    alert("समय-सारणी तैयार करने में त्रुटि: " + (err.message || "कृपया पुनः प्रयास करें।"));
    console.error("Auto generate schedule error:", err);
  } finally {
    hideLoadingOverlay();
  }
}

/**
 * Toggle Task Complete
 */
async function handleToggleReminder(reminderId) {
  try {
    await AgriAPI.toggleReminder(reminderId);
    await loadReminders();
  } catch (e) {
    alert("स्थिति बदलने में त्रुटि: " + e.message);
  }
}

/**
 * Delete Task
 */
async function handleDeleteReminder(reminderId) {
  if (!confirm("क्या आप यह कार्य सूची से हटाना चाहते हैं?")) return;
  try {
    await AgriAPI.deleteReminder(reminderId);
    await loadReminders();
  } catch (e) {
    alert("हटाने में त्रुटि: " + e.message);
  }
}

/**
 * Quick Selector Helpers
 */
function setQuickCrop(cropName) {
  const select = document.getElementById("schedule-crop-name");
  const custom = document.getElementById("schedule-custom-crop");
  if (select) {
    select.value = cropName;
    if (custom) custom.style.display = "none";
  }
}

function handleCropSelectChange(select) {
  const custom = document.getElementById("schedule-custom-crop");
  if (!custom) return;
  if (select.value === "__custom__") {
    custom.style.display = "block";
    custom.focus();
  } else {
    custom.style.display = "none";
  }
}

function setTodaySowingDate() {
  const input = document.getElementById("schedule-sowing-date");
  if (input) input.value = new Date().toISOString().split("T")[0];
}

function setPastSowingDays(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  const input = document.getElementById("schedule-sowing-date");
  if (input) input.value = d.toISOString().split("T")[0];
}

function setQuickAcres(acres) {
  const input = document.getElementById("schedule-acreage");
  if (input) input.value = acres;
}

/**
 * Manual Custom Reminder Modal
 */
function openAddModal() {
  const m = document.getElementById("add-modal");
  if (m) m.style.display = "flex";
}

function closeAddModal() {
  const m = document.getElementById("add-modal");
  if (m) m.style.display = "none";
}

async function handleSaveCustomReminder() {
  const title = document.getElementById("m-title")?.value?.trim();
  const type = document.getElementById("m-type")?.value || "general";
  const due = document.getElementById("m-due")?.value?.trim() || "शीघ्र";
  const desc = document.getElementById("m-desc")?.value?.trim() || "";

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
    if (document.getElementById("m-title")) document.getElementById("m-title").value = "";
    if (document.getElementById("m-desc")) document.getElementById("m-desc").value = "";
    await loadReminders();
  } catch (e) {
    alert("अनुस्मारक जोड़ने में त्रुटि: " + e.message);
  }
}

/**
 * Natural Language Voice/Text Crop Sowing Scheduler
 * Automatically recognizes single or multi-crop statements (e.g. "today sowed 3 acres wheat and 2 acres mustard")
 */
function fillNlpPrompt(promptText) {
  const input = document.getElementById("nlp-crop-input");
  if (input) {
    input.value = promptText;
    input.focus();
  }
}

async function handleNaturalLanguageSowing() {
  const input = document.getElementById("nlp-crop-input");
  const text = input ? input.value.trim() : "";
  if (!text) {
    alert("कृपया अपनी फसल व बुवाई का विवरण लिखें या बोलें (उदा. 'आज 3 एकड़ गेहूं और 2 एकड़ सरसों बोया')।");
    if (input) input.focus();
    return;
  }

  const btn = document.getElementById("btn-nlp-generate");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "<span>⏳</span> <span>AI विश्लेषण हो रहा है...</span>";
  }

  const overlay = document.getElementById("loading-overlay");
  const statusText = document.getElementById("loading-status-text");
  if (overlay) overlay.style.display = "flex";
  if (statusText) {
    statusText.innerText = `AgriGo AI आपके विवरण "${text}" का विश्लेषण कर मौसम व शस्य-विज्ञान अनुसार समय-सारणी बना रहा है...`;
  }

  try {
    const farmerId = currentFarmerUser ? currentFarmerUser.id : null;
    const res = await AgriAPI.createNaturalReminder(text, farmerId);
    
    if (overlay) overlay.style.display = "none";
    if (input) input.value = "";

    const desc = res?.reminder?.description || res?.reminder?.title || "समय-सारणी तैयार!";
    alert(desc);
    await loadReminders();

    const stagesSection = document.getElementById("process-stages-container");
    if (stagesSection) {
      stagesSection.scrollIntoView({ behavior: "smooth" });
    }
  } catch (err) {
    if (overlay) overlay.style.display = "none";
    alert("त्रुटि: " + (err.message || "कैलेंडर बनाने में समस्या आई। कृपया पुनः प्रयास करें।"));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "<span>⚡</span> <span>AI से तुरंत कैलेंडर बनाएं ➔</span>";
    }
  }
}

/**
 * Clear All Reminders (Fresh Start)
 */
async function handleClearAllReminders() {
  if (!confirm("क्या आप वर्तमान फसल का पूरा कैलेंडर हटाकर नया शुरू करना चाहते हैं?")) return;
  try {
    const fid = currentFarmerUser ? currentFarmerUser.id : "farmer-guest";
    await AgriAPI.clearAllReminders(fid);
    allReminders = [];
    updateMetricsAndHero();
    renderProcessStages();
    renderAllRemindersList();
    alert("✓ समस्त अनुस्मारक हटा दिए गए हैं। अब आप नई फसल का चयन कर सकते हैं।");
  } catch (e) {
    alert("रीसेट करने में त्रुटि: " + e.message);
  }
}

/**
 * Native Web Speech API Voice Dictation in Hindi
 */
function toggleVoiceInput(inputId) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    alert("आपके ब्राउज़र में आवाज़ पहचान (Voice Input) समर्थित नहीं है। कृपया लिखकर बताएं।");
    return;
  }
  const recognition = new SpeechRec();
  recognition.lang = "hi-IN";
  recognition.interimResults = false;

  const micBtn = document.getElementById("btn-voice-mic");
  if (micBtn) {
    micBtn.style.background = "#FEE2E2";
    micBtn.innerHTML = "🔴 बोलें...";
  }

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    const input = document.getElementById(inputId);
    if (input) {
      input.value = transcript;
      handleNaturalLanguageSowing();
    }
  };

  recognition.onerror = () => {
    if (micBtn) {
      micBtn.style.background = "";
      micBtn.innerHTML = "🎤";
    }
  };

  recognition.onend = () => {
    if (micBtn) {
      micBtn.style.background = "";
      micBtn.innerHTML = "🎤";
    }
  };

  recognition.start();
}


