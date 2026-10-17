/**
 * AgriGo — Modern Farmer-First Crop Reminders & Schedule Controller
 * Clean, intuitive, 1-tap task completion with Hindi Voice & ICAR Agronomy
 */

let allReminders = [];
let currentFilter = "all";
let currentFarmerUser = null;
let currentAcreage = 2.5;
let currentCropName = "गेहूं (Wheat)";
let speechRecognitionInstance = null;
let isListening = false;

function isTaskCompleted(r) {
  return !!(r && (r.is_completed === 1 || r.is_completed === true || r.is_completed === "1" || r.is_completed === "true"));
}

function showLoading(title, desc) {
  const overlay = document.getElementById("modal-loading-overlay");
  const t = document.getElementById("loading-title");
  const d = document.getElementById("loading-desc");
  if (t && title) t.innerText = title;
  if (d && desc) d.innerText = desc;
  if (overlay) overlay.classList.add("active");
}

function hideLoading() {
  const overlay = document.getElementById("modal-loading-overlay");
  if (overlay) overlay.classList.remove("active");
}

async function initRemindersPage() {
  hideLoading();
  initFormDefaults();
  await checkFarmerAuth();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initRemindersPage);
} else {
  initRemindersPage();
}

window.addEventListener("pageshow", async () => {
  hideLoading();
  await checkFarmerAuth();
});

function initFormDefaults() {
  const today = new Date().toISOString().split("T")[0];
  const sowingDate = document.getElementById("modal-sowing-date");
  if (sowingDate && !sowingDate.value) sowingDate.value = today;
  const customDue = document.getElementById("c-due");
  if (customDue && !customDue.value) customDue.value = today;
}

async function checkFarmerAuth() {
  try {
    const meRes = await AgriAPI.getMe().catch(() => null);
    if (meRes && meRes.authenticated && meRes.user) {
      currentFarmerUser = meRes.user;
      if (currentFarmerUser.farm_area) {
        currentAcreage = parseFloat(currentFarmerUser.farm_area) || 2.5;
      }
      if (currentFarmerUser.primary_crop) {
        currentCropName = currentFarmerUser.primary_crop;
      }
    } else {
      currentFarmerUser = {
        id: "farmer-guest",
        name: "किसान साथी",
        farm_area: 2.5,
        primary_crop: "गेहूं (Wheat)"
      };
    }
  } catch (err) {
    currentFarmerUser = {
      id: "farmer-guest",
      name: "किसान साथी",
      farm_area: 2.5,
      primary_crop: "गेहूं (Wheat)"
    };
  }

  updateHeroBadge();
  await loadReminders();
}

function updateHeroBadge() {
  const badge = document.getElementById("hero-crop-badge");
  if (badge) {
    badge.innerText = `${currentCropName} • ${currentAcreage} एकड़`;
  }
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
        allReminders = (res && res.reminders) ? res.reminders : [];
      }
    } else {
      allReminders = res.reminders;
    }
  } catch (e) {
    console.warn("Notice loading reminders:", e);
  } finally {
    updateTaskMetrics();
    renderTasksView();
  }
}

/**
 * Calculates metrics and updates the 3 summary stat cards & filter pill counts
 */
function updateTaskMetrics() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let todayCount = 0;
  let upcomingCount = 0;
  let completedCount = 0;
  let irrCount = 0;
  let fertCount = 0;
  let pestCount = 0;

  allReminders.forEach(r => {
    const isDone = isTaskCompleted(r);
    const t = (r.reminder_type || r.category || "").toLowerCase();
    const title = (r.title || "").toLowerCase();

    if (t.includes("irrigation") || title.includes("सिंचाई") || title.includes("पानी")) {
      irrCount++;
    } else if (t.includes("fertilizer") || title.includes("खाद") || title.includes("यूरिया") || title.includes("dap")) {
      fertCount++;
    } else if (t.includes("pest") || title.includes("कीट") || title.includes("रोग") || title.includes("स्प्रे") || title.includes("छिड़काव")) {
      pestCount++;
    }

    if (isDone) {
      completedCount++;
      return;
    }

    // Date urgency calculation
    let isTodayDue = false;
    const match = (r.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
    if (match) {
      const due = new Date(match[0]);
      due.setHours(0, 0, 0, 0);
      const diff = Math.round((due - today) / (1000 * 60 * 60 * 24));
      if (diff <= 0) {
        isTodayDue = true;
      }
    } else if ((r.due_date || "").includes("आज") || (r.due_date || "").includes("देय") || (r.due_date || "").includes("CRI")) {
      isTodayDue = true;
    }

    if (isTodayDue) {
      todayCount++;
    } else {
      upcomingCount++;
    }
  });

  // Update top cards
  const elToday = document.getElementById("stat-today-count");
  if (elToday) elToday.innerText = todayCount;
  const elUp = document.getElementById("stat-upcoming-count");
  if (elUp) elUp.innerText = upcomingCount;
  const elDone = document.getElementById("stat-completed-count");
  if (elDone) elDone.innerText = completedCount;

  // Update filter pills
  const pAll = document.getElementById("pill-all-count");
  if (pAll) pAll.innerText = allReminders.length;
  const pToday = document.getElementById("pill-today-count");
  if (pToday) pToday.innerText = todayCount;
  const pIrr = document.getElementById("pill-irr-count");
  if (pIrr) pIrr.innerText = irrCount;
  const pFert = document.getElementById("pill-fert-count");
  if (pFert) pFert.innerText = fertCount;
  const pPest = document.getElementById("pill-pest-count");
  if (pPest) pPest.innerText = pestCount;
  const pDone = document.getElementById("pill-done-count");
  if (pDone) pDone.innerText = completedCount;
}

/**
 * Renders the main task sections based on active filter
 */
function renderTasksView() {
  const sectionToday = document.getElementById("section-today");
  const sectionUpcoming = document.getElementById("section-upcoming");
  const sectionCompleted = document.getElementById("section-completed");
  const gridToday = document.getElementById("grid-today");
  const gridUpcoming = document.getElementById("grid-upcoming");
  const gridCompleted = document.getElementById("grid-completed");
  const emptyState = document.getElementById("tasks-empty-state");

  if (!gridToday || !gridUpcoming || !gridCompleted) return;

  gridToday.innerHTML = "";
  gridUpcoming.innerHTML = "";
  gridCompleted.innerHTML = "";

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Grouping arrays
  const todayTasks = [];
  const upcomingTasks = [];
  const completedTasks = [];

  // Filter tasks
  let activeList = allReminders;
  if (currentFilter === "completed") {
    activeList = allReminders.filter(r => isTaskCompleted(r));
  } else if (currentFilter === "irrigation") {
    activeList = allReminders.filter(r => (r.reminder_type || "").includes("irrigation") || (r.title || "").includes("सिंचाई"));
  } else if (currentFilter === "fertilizer") {
    activeList = allReminders.filter(r => (r.reminder_type || "").includes("fertilizer") || (r.title || "").includes("खाद") || (r.title || "").includes("यूरिया") || (r.title || "").includes("dap"));
  } else if (currentFilter === "pest") {
    activeList = allReminders.filter(r => (r.reminder_type || "").includes("pest") || (r.title || "").includes("कीट") || (r.title || "").includes("रोग") || (r.title || "").includes("स्प्रे"));
  }

  // Classify each task
  activeList.forEach(r => {
    if (isTaskCompleted(r)) {
      completedTasks.push(r);
      return;
    }

    let isTodayDue = false;
    const match = (r.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
    if (match) {
      const due = new Date(match[0]);
      due.setHours(0, 0, 0, 0);
      const diff = Math.round((due - today) / (1000 * 60 * 60 * 24));
      if (diff <= 0) isTodayDue = true;
    } else if ((r.due_date || "").includes("आज") || (r.due_date || "").includes("देय") || (r.due_date || "").includes("CRI")) {
      isTodayDue = true;
    }

    if (isTodayDue) {
      todayTasks.push(r);
    } else {
      upcomingTasks.push(r);
    }
  });

  // Sort upcoming chronologically
  upcomingTasks.sort((a, b) => {
    const da = (a.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
    const db = (b.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
    if (da && db) return new Date(da[0]) - new Date(db[0]);
    return 0;
  });

  // Handle specific filter views
  if (currentFilter === "today") {
    sectionToday.style.display = todayTasks.length > 0 ? "block" : "none";
    sectionUpcoming.style.display = "none";
    sectionCompleted.style.display = "none";
  } else if (currentFilter === "completed") {
    sectionToday.style.display = "none";
    sectionUpcoming.style.display = "none";
    sectionCompleted.style.display = "block";
  } else {
    // 'all', 'irrigation', 'fertilizer', 'pest'
    sectionToday.style.display = todayTasks.length > 0 ? "block" : "none";
    sectionUpcoming.style.display = upcomingTasks.length > 0 ? "block" : "none";
    sectionCompleted.style.display = completedTasks.length > 0 ? "block" : "none";
  }

  // Populate Today Grid
  todayTasks.forEach(r => {
    gridToday.appendChild(buildTaskCardElement(r, true));
  });
  const todayCountEl = document.getElementById("today-section-count");
  if (todayCountEl) todayCountEl.innerText = `${todayTasks.length} कार्य लंबित`;

  // Populate Upcoming Grid
  upcomingTasks.forEach(r => {
    gridUpcoming.appendChild(buildTaskCardElement(r, false));
  });
  const upCountEl = document.getElementById("upcoming-section-count");
  if (upCountEl) upCountEl.innerText = `${upcomingTasks.length} कार्य निर्धारित`;

  // Populate Completed Grid
  completedTasks.forEach(r => {
    gridCompleted.appendChild(buildTaskCardElement(r, false));
  });
  const doneCountEl = document.getElementById("completed-section-count");
  if (doneCountEl) doneCountEl.innerText = `${completedTasks.length} कार्य पूर्ण`;

  // Empty state check
  const totalShown = todayTasks.length + upcomingTasks.length + completedTasks.length;
  if (emptyState) {
    emptyState.style.display = totalShown === 0 ? "block" : "none";
  }
}

/**
 * Builds a single task DOM card element
 */
function buildTaskCardElement(r, isToday) {
  const isDone = isTaskCompleted(r);
  const card = document.createElement("div");
  card.className = `task-card ${isToday && !isDone ? 'is-today' : ''} ${isDone ? 'is-completed' : ''}`;
  card.id = `task-card-${r.id}`;

  // Category Tag setup
  const t = (r.reminder_type || r.category || "general").toLowerCase();
  const titleStr = (r.title || "").toLowerCase();
  let catClass = "cat-general";
  let catIcon = "📋";
  let catLabel = "कृषि कार्य";

  if (t.includes("irrigation") || titleStr.includes("सिंचाई") || titleStr.includes("पानी")) {
    catClass = "cat-irrigation";
    catIcon = "💧";
    catLabel = "सिंचाई";
  } else if (t.includes("fertilizer") || titleStr.includes("खाद") || titleStr.includes("यूरिया") || titleStr.includes("dap")) {
    catClass = "cat-fertilizer";
    catIcon = "🌱";
    catLabel = "खाद व पोषण";
  } else if (t.includes("pest") || titleStr.includes("कीट") || titleStr.includes("रोग") || titleStr.includes("स्प्रे")) {
    catClass = "cat-pest";
    catIcon = "🛡️";
    catLabel = "पादप सुरक्षा";
  }

  // Urgency Badge setup
  let urgClass = "urg-upcoming";
  let urgLabel = r.due_date || "शीघ्र";

  if (isDone) {
    urgClass = "urg-done";
    urgLabel = "✓ संपन्न";
  } else {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const match = (r.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
    if (match) {
      const due = new Date(match[0]);
      due.setHours(0, 0, 0, 0);
      const diff = Math.round((due - today) / (1000 * 60 * 60 * 24));
      if (diff < 0) {
        urgClass = "urg-today";
        urgLabel = `⚠️ ${Math.abs(diff)} दिन पूर्व`;
      } else if (diff === 0) {
        urgClass = "urg-today";
        urgLabel = "🔥 आज ही देय";
      } else if (diff === 1) {
        urgClass = "urg-tomorrow";
        urgLabel = "⏳ कल देय";
      } else {
        urgClass = "urg-upcoming";
        urgLabel = `📅 ${diff} दिन शेष`;
      }
    } else if ((r.due_date || "").includes("आज") || (r.due_date || "").includes("देय")) {
      urgClass = "urg-today";
      urgLabel = "🔥 आज ही देय";
    }
  }

  // Dosage highlight
  let doseHtml = "";
  if (r.dosage_info) {
    doseHtml = `<div class="task-dose-box">⚖️ अनुशंसित खुराक: ${r.dosage_info}</div>`;
  }

  card.innerHTML = `
    <div>
      <div class="task-header">
        <div class="task-badges">
          <span class="badge-category ${catClass}">${catIcon} ${catLabel}</span>
          <span class="badge-urgency ${urgClass}">${urgLabel}</span>
        </div>
      </div>

      <h4 class="task-title">${r.title}</h4>
      <p class="task-desc">${r.description || 'विशिष्ट निर्देश उपलब्ध नहीं हैं।'}</p>
      ${doseHtml}
    </div>

    <div class="task-footer">
      <span class="task-due-text">तारीख: ${r.due_date || 'शीघ्र'}</span>
      <div class="task-actions">
        <button 
          type="button" 
          class="btn-toggle-done ${isDone ? 'done-active' : ''}" 
          onclick="handleToggleTask('${r.id}')"
          aria-label="${isDone ? 'पुनः सक्रिय करें' : 'कार्य संपन्न चिह्नित करें'}"
        >
          ${isDone ? '↺ सक्रिय करें' : '✓ पूर्ण'}
        </button>
        <button 
          type="button" 
          class="btn-del-task" 
          onclick="handleDeleteTask('${r.id}')"
          title="कार्य हटाएं"
        >
          🗑️
        </button>
      </div>
    </div>
  `;

  return card;
}

/**
 * Filter change
 */
function setRemFilter(filterType, btn) {
  currentFilter = filterType;
  document.querySelectorAll(".rem-filter-pill").forEach(p => p.classList.remove("active"));
  if (btn) btn.classList.add("active");
  renderTasksView();
}

/**
 * 1-Tap Toggle Task Completion
 */
async function handleToggleTask(reminderId) {
  // Optimistic local update
  const target = allReminders.find(r => r.id === reminderId);
  if (target) {
    target.is_completed = isTaskCompleted(target) ? 0 : 1;
    updateTaskMetrics();
    renderTasksView();
  }

  try {
    await AgriAPI.toggleReminder(reminderId);
    // Refresh to sync with server
    const fid = currentFarmerUser ? currentFarmerUser.id : "farmer-guest";
    const res = await AgriAPI.getFarmerReminders(fid).catch(() => null);
    if (res && res.reminders) {
      allReminders = res.reminders;
      updateTaskMetrics();
      renderTasksView();
    }
  } catch (e) {
    console.error("Toggle error:", e);
    // Revert if error
    if (target) {
      target.is_completed = isTaskCompleted(target) ? 0 : 1;
      updateTaskMetrics();
      renderTasksView();
    }
    alert("स्थिति बदलने में त्रुटि: " + e.message);
  }
}

/**
 * Delete Task
 */
async function handleDeleteTask(reminderId) {
  if (!confirm("क्या आप यह कार्य सूची से हटाना चाहते हैं?")) return;
  try {
    await AgriAPI.deleteReminder(reminderId);
    allReminders = allReminders.filter(r => r.id !== reminderId);
    updateTaskMetrics();
    renderTasksView();
  } catch (e) {
    alert("हटाने में त्रुटि: " + e.message);
  }
}

/**
 * Quick Add via Natural Language Voice/Text
 */
function fillQuickExample(text) {
  const input = document.getElementById("nlp-quick-input");
  if (input) {
    input.value = text;
    input.focus();
  }
}

async function handleQuickAddNLP() {
  const input = document.getElementById("nlp-quick-input");
  const text = input ? input.value.trim() : "";
  if (!text) {
    alert("कृपया कार्य का विवरण लिखें या बोलें (उदा. 'कल सुबह यूरिया डालना')।");
    if (input) input.focus();
    return;
  }

  const btn = document.getElementById("btn-quick-submit");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = "<span>⏳</span> <span>जोड़ा जा रहा है...</span>";
  }

  showLoading("⚡ AI कार्य विश्लेषण...", `AgriGo AI आपके विवरण "${text}" को समझकर शेड्यूल में जोड़ रहा है...`);

  try {
    const fid = currentFarmerUser ? currentFarmerUser.id : "farmer-guest";
    const res = await AgriAPI.createNaturalReminder(text, fid);
    hideLoading();
    if (input) input.value = "";

    const msg = res?.reminder?.description || res?.reminder?.title || "कार्य सफलतापूर्वक जोड़ा गया!";
    alert("✓ " + msg);
    await loadReminders();
  } catch (err) {
    hideLoading();
    alert("त्रुटि: " + (err.message || "कार्य जोड़ने में समस्या आई।"));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = "<span>+</span> <span>कार्य जोड़ें ➔</span>";
    }
  }
}

/**
 * Voice Recognition for Quick Bar
 */
function toggleQuickVoice() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    alert("आपके ब्राउज़र में आवाज़ पहचान (Voice Input) समर्थित नहीं है। कृपया लिखकर बताएं।");
    return;
  }

  const micBtn = document.getElementById("btn-quick-mic");

  if (isListening && speechRecognitionInstance) {
    speechRecognitionInstance.stop();
    return;
  }

  const recognition = new SpeechRec();
  recognition.lang = "hi-IN";
  recognition.interimResults = false;
  speechRecognitionInstance = recognition;

  recognition.onstart = () => {
    isListening = true;
    if (micBtn) {
      micBtn.classList.add("recording");
      micBtn.innerHTML = "🔴 <span>सुन रहे हैं...</span>";
    }
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    const input = document.getElementById("nlp-quick-input");
    if (input) {
      input.value = transcript;
      handleQuickAddNLP();
    }
  };

  recognition.onerror = () => {
    isListening = false;
    if (micBtn) {
      micBtn.classList.remove("recording");
      micBtn.innerHTML = "🎤 <span>बोलें</span>";
    }
  };

  recognition.onend = () => {
    isListening = false;
    if (micBtn) {
      micBtn.classList.remove("recording");
      micBtn.innerHTML = "🎤 <span>बोलें</span>";
    }
  };

  recognition.start();
}

/**
 * Schedule Generator Modal Handlers
 */
function openScheduleGeneratorModal() {
  const m = document.getElementById("modal-schedule-gen");
  if (m) {
    m.classList.add("active");
    // Pre-fill crop and acres
    const select = document.getElementById("modal-crop-select");
    if (select) select.value = currentCropName;
    const acres = document.getElementById("modal-acreage");
    if (acres) acres.value = currentAcreage;
  }
}

function closeScheduleGeneratorModal() {
  const m = document.getElementById("modal-schedule-gen");
  if (m) m.classList.remove("active");
}

function handleModalCropSelect(val) {
  const custom = document.getElementById("modal-custom-crop");
  if (custom) {
    custom.style.display = (val === "__custom__") ? "block" : "none";
    if (val === "__custom__") custom.focus();
  }
}

function selectCropFromChip(cropName) {
  const select = document.getElementById("modal-crop-select");
  const custom = document.getElementById("modal-custom-crop");
  if (select) {
    select.value = cropName;
    if (custom) custom.style.display = "none";
  }
  document.querySelectorAll(".crop-chip-btn").forEach(b => {
    b.classList.toggle("selected", b.innerText.includes(cropName.split(" ")[0]));
  });
}

function setModalSowingDate(pastDays) {
  const input = document.getElementById("modal-sowing-date");
  if (!input) return;
  const d = new Date();
  if (pastDays > 0) d.setDate(d.getDate() - pastDays);
  input.value = d.toISOString().split("T")[0];
}

function setModalAcreage(acres) {
  const input = document.getElementById("modal-acreage");
  if (input) input.value = acres;
}

async function handleModalGenerateSchedule(e) {
  e.preventDefault();

  const select = document.getElementById("modal-crop-select");
  let cropVal = select ? select.value : "";
  if (cropVal === "__custom__") {
    const custom = document.getElementById("modal-custom-crop");
    cropVal = custom ? custom.value.trim() : "";
  }
  if (!cropVal) {
    alert("कृपया फसल का नाम चुनें या लिखें।");
    return;
  }

  const dateInput = document.getElementById("modal-sowing-date");
  const dateVal = dateInput ? dateInput.value : "";
  if (!dateVal) {
    alert("कृपया बुवाई या रोपाई की तारीख चुनें।");
    return;
  }

  const acreInput = document.getElementById("modal-acreage");
  const acreVal = acreInput ? parseFloat(acreInput.value) : 1.0;
  if (!acreVal || acreVal <= 0) {
    alert("कृपया मान्य एकड़ दर्ज करें।");
    return;
  }

  currentCropName = cropVal;
  currentAcreage = acreVal;
  updateHeroBadge();

  closeScheduleGeneratorModal();
  showLoading("⚡ AI संपूर्ण कैलेंडर तैयार कर रहा है...", `ICAR शस्य-विज्ञान डेटाबेस से ${cropVal} (${acreVal} एकड़) हेतु सिंचाई, खाद व कीट सुरक्षा की गणना हो रही है...`);

  try {
    const fid = currentFarmerUser ? currentFarmerUser.id : "farmer-guest";
    const res = await AgriAPI.generateCropSchedule(cropVal, dateVal, acreVal, fid);
    hideLoading();
    alert(`🎉 बधाई हो! ${cropVal} के लिए ${acreVal} एकड़ की संपूर्ण समय-सारणी (${res?.schedule?.total_tasks_created || 15} कार्य) सफलतापूर्वक तैयार कर ली गई है!`);
    await loadReminders();
  } catch (err) {
    hideLoading();
    alert("समय-सारणी तैयार करने में त्रुटि: " + (err.message || "कृपया पुनः प्रयास करें।"));
  }
}

/**
 * Custom Task Modal Handlers
 */
function openAddCustomModal() {
  const m = document.getElementById("modal-custom-task");
  if (m) m.classList.add("active");
}

function closeAddCustomModal() {
  const m = document.getElementById("modal-custom-task");
  if (m) m.classList.remove("active");
}

async function handleSaveCustomTask(e) {
  e.preventDefault();
  const title = document.getElementById("c-title")?.value?.trim();
  const type = document.getElementById("c-type")?.value || "general";
  const due = document.getElementById("c-due")?.value?.trim();
  const desc = document.getElementById("c-desc")?.value?.trim() || "";

  if (!title) {
    alert("कृपया कार्य का नाम लिखें।");
    return;
  }

  try {
    const fid = currentFarmerUser ? currentFarmerUser.id : "farmer-guest";
    await AgriAPI.createCustomReminder({
      farmer_id: fid,
      title: title,
      description: desc,
      due_date: due || "शीघ्र",
      reminder_type: type,
      priority: "high"
    });
    closeAddCustomModal();
    if (document.getElementById("c-title")) document.getElementById("c-title").value = "";
    if (document.getElementById("c-desc")) document.getElementById("c-desc").value = "";
    await loadReminders();
  } catch (err) {
    alert("अनुस्मारक जोड़ने में त्रुटि: " + err.message);
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
    updateTaskMetrics();
    renderTasksView();
    alert("✓ समस्त कार्य हटा दिए गए हैं। अब आप नया कैलेंडर बना सकते हैं।");
  } catch (e) {
    alert("रीसेट करने में त्रुटि: " + e.message);
  }
}
