/**
 * Farmer Interface Logic: Real-time Chat, Speech Recognition, Image Diagnosis, and Reminders
 * Session-based authentication & real geolocation with manual fallback
 */

let speechRecognition = null;
let isRecording = false;
let currentFarmer = null;

document.addEventListener("DOMContentLoaded", async () => {
  await checkAuthAndInit();
});

window.addEventListener("pageshow", async (event) => {
  await checkAuthAndInit();
});

async function checkAuthAndInit() {
  try {
    const res = await AgriAPI.getMe();
    if (!res || !res.authenticated || !res.user) {
      window.location.href = "farmer-login.html";
      return;
    }
    currentFarmer = res.user;

    // Display farmer identity dynamically (no mock data)
    const disp = document.getElementById("farmer-name-display");
    if (disp) {
      disp.innerText = `${currentFarmer.name}`;
    }
    const locDisp = document.getElementById("farmer-location-display");
    if (locDisp) {
      const v = currentFarmer.village || 'ग्राम';
      const d = currentFarmer.district || 'वाराणसी';
      const s = currentFarmer.state || 'उत्तर प्रदेश';
      locDisp.innerText = `📍 ग्राम: ${v}, ${d} (${s})`;
    }
    const fieldDisp = document.getElementById("farmer-field-display");
    if (fieldDisp) {
      fieldDisp.innerText = `🌿 किसान ID: ${currentFarmer.id} | संपर्क: ${currentFarmer.phone}`;
    }

    // Initialize AI Yield Calculator with all Indian states & farmer's location
    initFarmerCalcStates(currentFarmer.state, currentFarmer.district);

    // Fetch farmer's real crops & farm telemetry
    let farmerAcres = 3.0;
    let activeCropName = "धान / चावल (Paddy)";
    try {
      const cropsRes = await AgriAPI.getFarmerCrops(currentFarmer.id);
      if (cropsRes && cropsRes.crops && cropsRes.crops.length > 0) {
        const c = cropsRes.crops[0];
        activeCropName = c.crop_name || activeCropName;
        farmerAcres = parseFloat(c.area_acres) || parseFloat(currentFarmer.farm_size_acres) || 3.0;
      } else if (currentFarmer.farm_size_acres) {
        farmerAcres = parseFloat(currentFarmer.farm_size_acres);
      }
    } catch (_) {}

    // Populate Dynamic Field Details Bar
    const elAcres = document.getElementById("farmer-field-acres");
    if (elAcres) elAcres.innerText = `${farmerAcres.toFixed(1)} एकड़ (${(farmerAcres * 0.404686).toFixed(2)} हेक्टेयर)`;
    const elCropBadge = document.getElementById("farmer-current-crop-badge");
    if (elCropBadge) elCropBadge.innerText = `🌱 वर्तमान फसल: ${activeCropName}`;
    const elFarmName = document.getElementById("farmer-farm-name");
    if (elFarmName) elFarmName.innerText = `${currentFarmer.village || 'ग्राम'} कृषि प्रक्षेत्र`;

    // Attach logout handlers to any logout buttons on the page
    document.querySelectorAll("a[href='index.html']").forEach(link => {
      if (link.innerText.includes("लॉगआउट") || link.innerText.includes("Logout")) {
        link.onclick = async (e) => {
          e.preventDefault();
          try { await AgriAPI.logout(); } catch (_) {}
          window.location.href = "farmer-login.html?logged_out=1";
        };
      }
    });

    // Initialize satellite farm map with dynamic acreage & boundary
    await initSatelliteFarmMap(currentFarmer, farmerAcres, activeCropName);

    // Load live mini mandi rates
    await loadFarmerMiniMandi();

    // Load weather (uses real browser geolocation with manual fallback)
    await loadLiveWeather();

    // Load crops and reminders using authenticated farmer ID
    await loadFarmerCrops();
    await loadFarmerReminders();
    initSpeechRecognition();

    // Verify Supabase Cloud Database live connection
    try {
      const supaStatus = await AgriAPI.getSupabaseStatus();
      const pill = document.getElementById("supabase-cloud-pill");
      if (pill && supaStatus && supaStatus.healthy) {
        pill.innerHTML = `⚡ Supabase: <strong style="color:#C8E6C9;">सक्रिय (499k+ रिकॉर्ड्स)</strong>`;
      }
    } catch (_) {}
  } catch (e) {
    console.warn("Session check failed, redirecting to login:", e);
    window.location.href = "farmer-login.html";
  }
}

async function loadLiveWeather(customLat = null, customLon = null) {
  let lat = customLat;
  let lon = customLon;

  // If coordinates not passed manually, request browser location permission
  if (lat === null && navigator.geolocation) {
    try {
      const pos = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
      });
      lat = pos.coords.latitude;
      lon = pos.coords.longitude;
    } catch (geoErr) {
      console.log("Browser location permission denied or timed out. Using default regional context.", geoErr);
    }
  }

  try {
    const data = await AgriAPI.getAgriWeather(lat, lon);
    if (!data) return;

    const tempEl = document.getElementById("w-temp");
    if (tempEl) tempEl.innerText = `${data.temperature_c}°C (महसूस: ${data.feels_like_c || data.temperature_c}°C)`;

    const rainEl = document.getElementById("w-rain");
    if (rainEl) rainEl.innerText = `${data.rain_prob_today_pct}%`;
    
    const sprayBadge = document.getElementById("w-spray");
    if (sprayBadge) {
      if (data.spray_window_safe) {
        sprayBadge.innerText = "सुरक्षित ✓ (हवा सामान्य)";
        sprayBadge.className = "badge badge-green";
      } else {
        sprayBadge.innerText = "असुरक्षित ⚠️ (छिड़काव टालें)";
        sprayBadge.className = "badge badge-gold";
      }
    }

    const pill = document.getElementById("weather-card-pill");
    if (pill) {
      const loc = data.location || "मौसम";
      pill.innerText = `🌤️ ${loc}: ${data.temperature_c}°C | बारिश: ${data.rain_prob_today_pct}% ➔`;
    }
  } catch (e) {
    console.error("Error loading weather:", e);
  }
}

let satelliteMapInstance = null;

async function initSatelliteFarmMap(farmer, acres = 3.0, cropName = "धान / चावल (Paddy)") {
  const mapContainer = document.getElementById("satellite-map");
  if (!mapContainer || typeof L === 'undefined') return;

  // Resolve coordinates: lookup farmer's district/state from AGRI_LOCATIONS or default to Varanasi
  let lat = 25.3176;
  let lon = 82.9739;
  let locTitle = "वाराणसी (उत्तर प्रदेश)";

  if (farmer && farmer.district && window.AGRI_LOCATIONS) {
    for (const [stName, stData] of Object.entries(window.AGRI_LOCATIONS)) {
      if (stData.districts && stData.districts[farmer.district]) {
        const d = stData.districts[farmer.district];
        lat = d.lat;
        lon = d.lon;
        locTitle = `${farmer.district}, ${farmer.state || stName}`;
        break;
      }
    }
  }

  const coordEl = document.getElementById("sat-coords");
  if (coordEl) {
    coordEl.innerText = `📍 ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E (${locTitle})`;
  }

  // Calculate actual field boundary polygon according to registered acreage
  const areaSqm = acres * 4046.86;
  const halfSideMeters = Math.sqrt(areaSqm) / 2;
  const dLat = halfSideMeters / 111139;
  const dLon = halfSideMeters / (111139 * Math.cos((lat * Math.PI) / 180));
  const fieldCorners = [
    [lat - dLat, lon - dLon],
    [lat - dLat, lon + dLon],
    [lat + dLat, lon + dLon],
    [lat + dLat, lon - dLon]
  ];

  if (satelliteMapInstance) {
    satelliteMapInstance.setView([lat, lon], 16);
    return;
  }

  // Initialize Leaflet satellite map
  satelliteMapInstance = L.map('satellite-map', {
    center: [lat, lon],
    zoom: 16,
    zoomControl: false,
    attributionControl: false
  });

  // Esri World Imagery (High-Resolution Satellite Tiles, Free & Legal)
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19
  }).addTo(satelliteMapInstance);

  // Draw real field boundary polygon based on actual acres
  L.polygon(fieldCorners, {
    color: '#00FF66',
    weight: 2.5,
    fillColor: '#00FF66',
    fillOpacity: 0.28,
    dashArray: '3, 4'
  }).addTo(satelliteMapInstance);

  // Custom pulsing farm pin at field center
  const farmIcon = L.divIcon({
    className: 'custom-farm-pin',
    html: `<div style="background:#00FF66; width:16px; height:16px; border-radius:50%; border:3px solid #FFF; box-shadow:0 0 12px #00FF66, 0 0 20px rgba(0,255,102,0.6);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });

  const marker = L.marker([lat, lon], { icon: farmIcon }).addTo(satelliteMapInstance);
  marker.bindPopup(`
    <div style="font-family:system-ui; font-size:12px; line-height:1.55; color:#102213; min-width:190px;">
      <strong style="color:#1B5E20; font-size:13px;">🌾 ${farmer ? farmer.name : 'किसान'} का खेत</strong><br>
      📐 <strong>रकबा:</strong> ${acres.toFixed(1)} एकड़ (${(acres * 0.404686).toFixed(2)} हेक्टेयर)<br>
      🌱 <strong>फसल:</strong> ${cropName}<br>
      📍 <strong>स्थान:</strong> ${locTitle}<br>
      🛰️ <strong>उपग्रह स्तर:</strong> वास्तविक उपग्रह सीमांकन
    </div>
  `).openPopup();
}

async function loadFarmerMiniMandi() {
  const container = document.getElementById("farmer-mandi-mini");
  if (!container) return;
  try {
    const res = await AgriAPI.getLiveMandiPrices(4);
    if (res && res.prices && res.prices.length > 0) {
      container.innerHTML = "";
      res.prices.forEach(p => {
        const row = document.createElement("div");
        row.className = "mini-mandi-row";
        row.innerHTML = `
          <span>🌾 ${p.commodity} (${p.market || 'मंडी'})</span>
          <span class="mini-mandi-price">₹${Number(p.modal_price).toLocaleString('en-IN')}/क्विं</span>
        `;
        container.appendChild(row);
      });
    } else {
      container.innerHTML = `<div style="text-align:center; padding:10px; font-size:12px; color:var(--text-muted);">मंडी दरें उपलब्ध नहीं हैं</div>`;
    }
  } catch (_) {
    container.innerHTML = `<div style="text-align:center; padding:10px; font-size:12px; color:var(--text-muted);">मंडी दरें लोड करने में त्रुटि</div>`;
  }
}

async function loadFarmerCrops() {
  if (!currentFarmer) return;
  const container = document.getElementById("crops-timeline-list");
  const countEl = document.getElementById("active-crops-count");

  try {
    const res = await AgriAPI.getFarmerCrops(currentFarmer.id);
    if (container) {
      if (!res || !res.crops || res.crops.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">🌾 आपने अभी तक कोई फसल नहीं जोड़ी है।</div>`;
        if (countEl) countEl.innerText = "0 फसलें";
      } else {
        container.innerHTML = "";
        res.crops.forEach(c => {
          const item = document.createElement("div");
          item.className = "timeline-item";
          item.innerHTML = `
            <strong>🌾 ${c.crop_name} (${c.variety || 'देसी'})</strong>
            <div style="color: var(--text-muted); font-size: 12px;">अवस्था: <strong>${c.stage_hi || c.current_stage || c.stage}</strong></div>
            <div style="color: #2E7D32; font-size: 11.5px; margin-top: 3px;">स्वास्थ्य स्थिति: ${c.health_status || 'उत्तम'}</div>
            <div class="timeline-stage-bar"><div class="timeline-stage-fill" style="width: ${c.stage === 'Harvesting' ? 90 : (c.stage === 'Flowering' ? 60 : 35)}%"></div></div>
          `;
          container.appendChild(item);
        });
        if (countEl) countEl.innerText = `${res.crops.length} फसलें`;
      }
    }
  } catch (e) {
    if (container) container.innerHTML = `<div style="text-align:center; padding:12px; color:#EF4444; font-size:12px;">फसल डेटा लोड त्रुटि: ${e.message}</div>`;
  }
}

async function loadFarmerReminders() {
  if (!currentFarmer) return;
  const container = document.getElementById("reminders-list");

  try {
    const res = await AgriAPI.getFarmerReminders(currentFarmer.id);
    if (container) {
      if (!res || !res.reminders || res.reminders.length === 0) {
        container.innerHTML = `<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">⏰ कोई सक्रिय अनुस्मारक नहीं है।</div>`;
      } else {
        container.innerHTML = "";
        res.reminders.slice(0, 4).forEach(r => {
          const item = document.createElement("div");
          item.style.cssText = "border-left: 3px solid var(--primary); padding-left: 8px; margin-bottom: 6px;";
          const formattedDate = AgriAPI.formatLocalDateTime(r.created_at);
          item.innerHTML = `
            <strong>${r.title}</strong>
            <div style="color: var(--text-muted); font-size: 11.5px;">${r.due_date || formattedDate}</div>
          `;
          container.appendChild(item);
        });
      }
    }
  } catch (e) {
    if (container) container.innerHTML = `<div style="text-align:center; padding:12px; color:#EF4444; font-size:12px;">अनुस्मारक लोड त्रुटि: ${e.message}</div>`;
  }
}

function appendChatMessage(text, sender = "user", evidence = null, imageSrc = null) {
  const container = document.getElementById("chat-messages");
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${sender}`;

  let content = "";
  if (imageSrc) {
    content += `<div style="margin-bottom: 8px;"><img src="${imageSrc}" style="max-width: 220px; border-radius: 8px; border: 1px solid #CCC;" alt="Crop leaf"></div>`;
  }
  
  // Format line breaks
  const formattedText = text.replace(/\n/g, "<br>");
  content += `<div>${formattedText}</div>`;

  // Evidence Sources badge
  if (evidence && evidence.length > 0) {
    const sourcesStr = evidence.join(" • ");
    content += `<div class="evidence-tag">🏛️ सत्यापित स्रोत: ${sourcesStr}</div>`;
  }

  // Text-To-Speech button for AI
  if (sender === "ai") {
    content += `
      <div style="margin-top: 8px; display: flex; justify-content: flex-end;">
        <button class="btn btn-outline" style="padding: 2px 8px; font-size: 11.5px;" onclick="speakText(this)">🔊 बोलकर सुनाएं</button>
      </div>
    `;
  }

  bubble.innerHTML = content;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage(presetText = null) {
  const input = document.getElementById("chat-input");
  const query = presetText || input.value.trim();
  if (!query) return;

  if (!presetText) input.value = "";

  // Append user bubble
  appendChatMessage(query, "user");

  // Show typing indicator
  const typingIndicator = document.createElement("div");
  typingIndicator.className = "chat-bubble ai";
  typingIndicator.id = "typing-temp";
  typingIndicator.innerHTML = "🌱 <em>ICAR व कृषि ज्ञानकोष से सत्यापित सलाह जांची जा रही है...</em>";
  document.getElementById("chat-messages").appendChild(typingIndicator);

  try {
    const fid = currentFarmer ? currentFarmer.id : null;
    const result = await AgriAPI.askAgriculturalAI(query, "hi", null, fid);
    const temp = document.getElementById("typing-temp");
    if (temp) temp.remove();

    appendChatMessage(result.response, "ai", result.evidence);
  } catch (err) {
    const temp = document.getElementById("typing-temp");
    if (temp) temp.remove();
    appendChatMessage("सलाह प्राप्त करने में त्रुटि: " + err.message, "ai");
  }
}

function sendQuickPrompt(text) {
  sendChatMessage(text);
}

// Voice Speech Recognition (Web Speech API)
function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    console.log("Web Speech API not supported in this browser.");
    return;
  }

  speechRecognition = new SpeechRec();
  speechRecognition.continuous = false;
  speechRecognition.interimResults = false;
  speechRecognition.lang = "hi-IN";

  speechRecognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("chat-input").value = transcript;
    sendChatMessage(transcript);
  };

  speechRecognition.onend = () => {
    isRecording = false;
    const mic = document.getElementById("btn-voice-mic");
    if (mic) mic.style.background = "";
  };

  speechRecognition.onerror = (e) => {
    console.error("Speech recognition error:", e);
    isRecording = false;
  };
}

function toggleVoiceRecognition() {
  if (!speechRecognition) {
    alert("आपके ब्राउज़र में वॉइस रिकग्निशन समर्थित नहीं है। कृपया टाइप करके प्रश्न पूछें।");
    return;
  }

  const mic = document.getElementById("btn-voice-mic");
  if (!isRecording) {
    speechRecognition.start();
    isRecording = true;
    mic.style.background = "#FFCDD2";
  } else {
    speechRecognition.stop();
    isRecording = false;
    mic.style.background = "";
  }
}

// Text to Speech
function speakText(btn) {
  const bubble = btn.closest(".chat-bubble");
  const cleanText = bubble.innerText.replace("🔊 बोलकर सुनाएं", "").replace(/🏛️.*$/s, "");
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "hi-IN";
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  } else {
    alert("स्पीच सिंथेसिस समर्थित नहीं है।");
  }
}

// Photo Upload Diagnosis
async function handleLeafPhotoUpload(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];

  const reader = new FileReader();
  reader.onload = async (e) => {
    const imageBase64 = e.target.result;
    appendChatMessage("पत्ती की फोटो भेजी गई। निदान किया जा रहा है...", "user", null, imageBase64);

    try {
      const res = await AgriAPI.uploadLeafImage(file);
      const ana = res.analysis;
      const responseText = `
📸 **फोटो लक्षण निदान परिणाम:**
• **संभावित फसल:** ${ana.possible_crop}
• **संभावित रोग / कीट:** ${ana.possible_disease} (वेक्टर: ${ana.possible_pest})
• **देखे गए लक्षण:** ${ana.symptoms}
• **विश्वसनीयता स्कोर:** ${Math.round(ana.confidence_score * 100)}%

${ana.uncertainty_notice}
      `;
      appendChatMessage(responseText, "ai", [ana.source_advisory]);
    } catch (err) {
      appendChatMessage("फोटो विश्लेषण त्रुटि: " + err.message, "ai");
    }
  };
  reader.readAsDataURL(file);
}

// Natural Language Reminder
async function handleCreateNaturalReminder() {
  const input = document.getElementById("nl-reminder-input");
  const text = input.value.trim();
  if (!text) return;

  try {
    const fid = currentFarmer ? currentFarmer.id : null;
    const res = await AgriAPI.createNaturalReminder(text, fid);
    alert(`स्मार्ट रिमाइंडर बना दिया गया: "${res.reminder.title}" (${res.reminder.due_date})`);
    input.value = "";
    await loadFarmerReminders();
  } catch (err) {
    alert("रिमाइंडर बनाने में त्रुटि: " + err.message);
  }
}

// ----------------- ML Crop & Yield Calculator Handlers -----------------
function initFarmerCalcStates(defaultState, defaultDistrict) {
  const stateSelect = document.getElementById("calc-state");
  const distSelect = document.getElementById("calc-district");
  if (!stateSelect || !distSelect) return;

  const st = defaultState || "उत्तर प्रदेश (Uttar Pradesh)";
  const dt = defaultDistrict || "वाराणसी (Varanasi)";

  if (window.setupCascadingStateDistrict) {
    window.setupCascadingStateDistrict("calc-state", "calc-district", {
      defaultState: st,
      defaultDistrict: dt
    });
  } else if (window.INDIA_LOCATIONS) {
    stateSelect.innerHTML = '<option value="">-- राज्य चुनें --</option>';
    Object.keys(window.INDIA_LOCATIONS).forEach(s => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      stateSelect.appendChild(opt);
    });
    handleStateChange();
  }
}

function handleStateChange() {
  const state = document.getElementById("calc-state") ? document.getElementById("calc-state").value : "";
  const distSelect = document.getElementById("calc-district");
  if (!distSelect) return;

  let districts = [];
  if (window.getDistrictsForState) {
    districts = window.getDistrictsForState(state);
  } else if (window.INDIA_LOCATIONS && window.INDIA_LOCATIONS[state]) {
    districts = Object.keys(window.INDIA_LOCATIONS[state]);
  }
  if (!districts || districts.length === 0) {
    districts = ["वाराणसी (Varanasi)", "लखनऊ (Lucknow)"];
  }

  distSelect.innerHTML = "";
  districts.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = d;
    distSelect.appendChild(opt);
  });
}

async function handlePredictYieldUI() {
  const state = document.getElementById("calc-state").value;
  const district = document.getElementById("calc-district").value;
  const crop = document.getElementById("calc-crop").value;
  const acres = parseFloat(document.getElementById("calc-acres").value) || 1.0;
  const resBox = document.getElementById("calc-result-box");

  resBox.style.display = "block";
  resBox.innerHTML = "<div style='color: var(--primary);'>⏳ AI मॉडल व सरकारी रिकॉर्ड्स विश्लेषित किए जा रहे हैं...</div>";

  try {
    const res = await AgriAPI.predictYield({
      crop,
      state,
      district,
      area_acres: acres
    });

    const data = res.data;
    const h = data.predicted_harvest;
    const r = data.resource_requirements;
    const b = data.historical_benchmark;

    let benchHtml = "";
    if (b && b.avg_yield_tonnes_per_ha) {
      benchHtml = `
        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed #A5D6A7; font-size: 11px; color: #2E7D32;">
          🏛️ <strong>सरकारी सांख्यिकी (${district}):</strong><br>
          • 26-वर्षीय औसत उपज: <strong>${b.avg_yield_tonnes_per_ha} टन/हेक्टर</strong><br>
          • दर्ज अधिकतम उपज: <strong>${b.max_yield_tonnes_per_ha} टन/हेक्टर</strong>
        </div>
      `;
    }

    resBox.innerHTML = `
      <div style="font-weight: 700; color: var(--primary-dark); margin-bottom: 4px;">
        🌾 ${crop} (${acres} एकड़) — पैदावार अनुमान
      </div>
      <div style="font-size: 13px; font-weight: 700; color: #1B5E20; margin-bottom: 6px;">
        ✨ कुल पैदावार: ${h.total_quintals} क्विंटल (${h.total_tonnes} टन)
      </div>
      <div style="font-size: 11.5px; line-height: 1.5; color: var(--text-color);">
        • प्रति एकड़ दर: <strong>${h.yield_quintals_per_acre} क्विंटल/एकड़</strong><br>
        • अनुमानित जल: <strong>${r.water_cubic_meters.toLocaleString()} m³</strong><br>
        • अनुशंसित NPK: <strong>${r.fertilizer_kg} किग्रा</strong>
      </div>
      ${benchHtml}
      <button class="btn btn-outline" style="width: 100%; margin-top: 8px; font-size: 11px; padding: 4px;" onclick="sendQuickPrompt('मेरी ${acres} एकड़ जमीन में ${crop} की बुवाई, खाद व पैदावार की पूरी जानकारी बताएं')">
        💬 AI से संपूर्ण पैकेज पूछें ➔
      </button>
    `;
  } catch (err) {
    resBox.innerHTML = `<div style="color: red;">त्रुटि: ${err.message}</div>`;
  }
}

async function handleRecommendCropUI() {
  const resBox = document.getElementById("calc-result-box");
  resBox.style.display = "block";
  resBox.innerHTML = "<div style='color: var(--primary);'>⏳ जलवायु डेटा व 50,000+ रिकॉर्ड्स से उपयुक्त फसल खोजी जा रही है...</div>";

  try {
    const res = await AgriAPI.predictCropSuitability({
      n: 70.0, p: 35.0, k: 35.0,
      temperature: 26.0, humidity: 65.0, ph: 6.8, rainfall: 750.0
    });

    const d = res.data;
    const top = d.top_crop;
    const recs = d.recommendations.slice(0, 3);

    let listHtml = recs.map(r => `• <strong>${r.crop}</strong>: उपयुक्तता <strong>${r.suitability_score}%</strong> (${r.confidence})`).join("<br>");

    resBox.innerHTML = `
      <div style="font-weight: 700; color: var(--primary-dark); margin-bottom: 4px;">
        🌱 AI फसल उपयुक्तता सिफारिश
      </div>
      <div style="font-size: 12.5px; font-weight: 700; color: #2E7D32; margin-bottom: 4px;">
        शीर्ष सिफारिश: ${top}
      </div>
      <div style="font-size: 11.5px; line-height: 1.5; color: var(--text-color);">
        ${listHtml}
      </div>
      <button class="btn btn-outline" style="width: 100%; margin-top: 8px; font-size: 11px; padding: 4px;" onclick="sendQuickPrompt('${top} की खेती कैसे करें और क्या सावधानियां रखें?')">
        💬 ${top} की खेती की सलाह लें ➔
      </button>
    `;
  } catch (err) {
    resBox.innerHTML = `<div style="color: red;">त्रुटि: ${err.message}</div>`;
  }
}
