/**
 * AgriGo Material 3 & Android 15 Weather Hub Controller
 * Coordinates with Open-Meteo Detailed API for Current, Hourly, Past 10 Days & Agromet Intelligence.
 */

let currentLat = 25.3176;
let currentLon = 82.9739;
let currentLocName = "वाराणसी, उत्तर प्रदेश";

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Cascading State -> District Selector
  if (window.setupCascadingStateDistrict) {
    window.setupCascadingStateDistrict("weather-state-select", "weather-district-select", {
      defaultState: "उत्तर प्रदेश (Uttar Pradesh)",
      defaultDistrict: "वाराणसी (Varanasi)",
      onSelect: (loc) => {
        switchLocation(loc.lat, loc.lon, loc.name, null);
      }
    });
  }

  loadWeatherData(currentLat, currentLon, currentLocName);
});

async function loadWeatherData(lat, lon, locName) {
  try {
    const heroLoc = document.getElementById("hero-loc-name");
    if (heroLoc) heroLoc.innerHTML = `📍 ${locName} <span style="font-size:12px; font-weight:normal; opacity:0.75;">(ताज़ा डेटा लोड हो रहा है...)</span>`;
    
    const data = await AgriAPI.getDetailedWeather(lat, lon);
    if (!data) {
      if (heroLoc) heroLoc.innerText = `📍 ${locName}`;
      return;
    }

    if (heroLoc) heroLoc.innerText = `📍 ${locName}`;
    const todayForecast = (data.forecast_7_days && data.forecast_7_days.length > 0) ? data.forecast_7_days[0] : null;
    const rainProb = todayForecast ? (todayForecast.rain_prob_pct || 0) : 0;

    renderCurrentWeather(data.current, locName, rainProb);
    render7DayForecast(data.forecast_7_days || []);
    renderHourlyForecast(data.hourly_24h || []);
    renderPast10Days(data.past_10_days || []);
    renderAgriIntelligence(data.agricultural_intelligence || {});

    document.getElementById("live-time-stamp").innerText = `अपडेटेड: ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

    if (window.AgriI18n && window.AgriI18n.applyTranslation) {
      window.AgriI18n.applyTranslation();
    }
  } catch (err) {
    console.error("Error loading detailed weather:", err);
  }
}

function renderCurrentWeather(curr, locName, rainProb = 0) {
  if (!curr) return;

  document.getElementById("hero-temp").innerText = `${Math.round(curr.temp)}°`;
  document.getElementById("hero-icon").innerText = curr.icon || "🌤️";
  document.getElementById("hero-condition").innerText = `${curr.condition_hi} (${curr.condition_en})`;

  document.getElementById("pill-wind").innerText = `${curr.wind_speed_kmh} km/h`;
  document.getElementById("pill-humidity").innerText = `${curr.humidity}%`;

  const rainPill = document.getElementById("pill-rain-prob");
  if (rainPill) {
    rainPill.innerText = `${rainProb}%`;
    rainPill.style.color = rainProb > 40 ? "#93C5FD" : "#FFFFFF";
  }

  const sprayEl = document.getElementById("pill-spray");
  if (curr.spray_safe) {
    sprayEl.innerText = "सुरक्षित ✓ (हवा अनुकूल)";
    sprayEl.style.color = "#89F8BE";
  } else {
    sprayEl.innerText = "असुरक्षित ⚠️ (हवा/बारिश)";
    sprayEl.style.color = "#FFDAD6";
  }

  const irrEl = document.getElementById("pill-irrigation");
  if (curr.irrigation_advisable) {
    irrEl.innerText = "सिंचाई अनुकूल ✓";
    irrEl.style.color = "#89F8BE";
  } else {
    irrEl.innerText = "सिंचाई टालें 🌧️ (बारिश की संभावना)";
    irrEl.style.color = "#FFDAD6";
  }

  // Trigger dynamic weather visuals according to real API response
  applyWeatherVisualTheme(curr, rainProb);
}

function applyWeatherVisualTheme(curr, rainProb) {
  const card = document.getElementById("hero-weather-card");
  const stage = document.getElementById("weather-fx-stage");
  if (!card || !stage) return;

  if (window._weatherRainAnimId) {
    cancelAnimationFrame(window._weatherRainAnimId);
    window._weatherRainAnimId = null;
  }

  card.classList.remove("fx-sunny", "fx-cloudy", "fx-rainy", "fx-stormy", "fx-foggy");
  document.body.classList.remove("sky-sunny", "sky-cloudy", "sky-rainy", "sky-stormy", "sky-foggy");
  stage.innerHTML = "";

  const condText = ((curr.condition_en || "") + " " + (curr.condition_hi || "")).toLowerCase();
  const code = curr.weather_code !== undefined ? curr.weather_code : 0;

  const isStorm = code === 95 || code === 96 || code === 99 || condText.includes("thunder") || condText.includes("storm") || condText.includes("तूफान");
  const isRain = isStorm || (code >= 51 && code <= 67) || (code >= 80 && code <= 82) || rainProb >= 60 || condText.includes("rain") || condText.includes("drizzle") || condText.includes("shower") || condText.includes("बारिश") || condText.includes("वर्षा");
  const isFog = (code === 45 || code === 48) || condText.includes("fog") || condText.includes("mist") || condText.includes("haze") || condText.includes("कोहरा") || condText.includes("धुंध");
  const isCloud = (code === 2 || code === 3) || condText.includes("cloud") || condText.includes("overcast") || condText.includes("बादल");

  if (isStorm) {
    card.classList.add("fx-stormy");
    document.body.classList.add("sky-stormy");
    stage.innerHTML = `
      <div class="fx-lightning"></div>
      <canvas id="fx-rain-canvas"></canvas>
    `;
    startRainCanvas(true);
  } else if (isRain) {
    card.classList.add("fx-rainy");
    document.body.classList.add("sky-rainy");
    stage.innerHTML = `<canvas id="fx-rain-canvas"></canvas>`;
    startRainCanvas(false);
  } else if (isFog) {
    card.classList.add("fx-foggy");
    document.body.classList.add("sky-foggy");
    stage.innerHTML = `<div class="fx-mist"></div>`;
  } else if (isCloud) {
    card.classList.add("fx-cloudy");
    document.body.classList.add("sky-cloudy");
    stage.innerHTML = `
      <div class="fx-cloud fx-cloud-1"></div>
      <div class="fx-cloud fx-cloud-2"></div>
      <div class="fx-cloud fx-cloud-3"></div>
    `;
  } else {
    // Sunny / Clear
    card.classList.add("fx-sunny");
    document.body.classList.add("sky-sunny");
    stage.innerHTML = `
      <div class="fx-sun-orb"></div>
      <div class="fx-sun-ray"></div>
    `;
  }
}

function startRainCanvas(isHeavy) {
  const canvas = document.getElementById("fx-rain-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width || 800;
  canvas.height = rect.height || 300;

  const drops = [];
  const dropCount = isHeavy ? 65 : 36;
  for (let i = 0; i < dropCount; i++) {
    drops.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      len: 12 + Math.random() * 10,
      spd: (isHeavy ? 9 : 6) + Math.random() * 4
    });
  }

  function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    for (let i = 0; i < drops.length; i++) {
      const d = drops[i];
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x - 2, d.y + d.len);
      d.y += d.spd;
      d.x -= 0.8;
      if (d.y > canvas.height) {
        d.y = -d.len;
        d.x = Math.random() * canvas.width;
      }
    }
    ctx.stroke();
    window._weatherRainAnimId = requestAnimationFrame(loop);
  }
  loop();
}

function render7DayForecast(days) {
  const container = document.getElementById("forecast-7d-list");
  if (!container) return;

  if (days.length === 0) {
    container.innerHTML = "<div style='text-align: center; color: var(--md-sys-color-outline); padding: 14px;'>पूर्वानुमान उपलब्ध नहीं है।</div>";
    return;
  }

  container.innerHTML = "";
  days.forEach((d, idx) => {
    const dateObj = new Date(d.date);
    const dayName = idx === 0 ? "आज (Today)" : (idx === 1 ? "कल (Tomorrow)" : dateObj.toLocaleDateString("hi-IN", { weekday: 'short', month: 'short', day: 'numeric' }));

    const row = document.createElement("div");
    row.className = "day-row";
    row.innerHTML = `
      <div class="day-name">${dayName}</div>
      <div class="day-icon-cond">
        <span style="font-size: 20px;">${d.icon}</span>
        <span>${d.condition_hi}</span>
        ${d.rain_prob_pct > 25 ? `<span style="font-size: 11.5px; color: #1976D2; font-weight: 700; margin-left: 6px;">💧 ${d.rain_prob_pct}%</span>` : ''}
      </div>
      <div class="day-temp-bar-container">
        <span style="opacity: 0.65; font-size: 13px;">${Math.round(d.min_temp)}°</span>
        <div style="flex: 1; height: 6px; background: rgba(0, 109, 68, 0.15); border-radius: 999px; position: relative; max-width: 60px;">
          <div style="position: absolute; left: 10%; right: 10%; top: 0; bottom: 0; background: var(--md-sys-color-primary); border-radius: 999px;"></div>
        </div>
        <span style="font-weight: 800; font-size: 14px;">${Math.round(d.max_temp)}°</span>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderHourlyForecast(hours) {
  const container = document.getElementById("hourly-track-container");
  if (!container) return;

  if (hours.length === 0) {
    container.innerHTML = "<div style='color: var(--md-sys-color-outline); padding: 14px;'>प्रति घंटा डेटा उपलब्ध नहीं है।</div>";
    return;
  }

  container.innerHTML = "";
  hours.forEach((h, idx) => {
    const card = document.createElement("div");
    card.className = `hourly-card ${idx === 0 ? 'now' : ''}`;
    card.innerHTML = `
      <div class="hourly-time">${idx === 0 ? 'अभी' : h.time}</div>
      <div style="font-size: 24px;">${h.icon}</div>
      <div class="hourly-temp">${Math.round(h.temp)}°</div>
      <div style="font-size: 11px; opacity: 0.85; color: ${h.rain_prob > 30 ? '#1565C0' : 'inherit'}; font-weight: 600;">
        💧 ${h.rain_prob}%
      </div>
      <span class="hourly-spray-badge ${h.spray_safe ? 'spray-ok' : 'spray-bad'}">
        ${h.spray_safe ? 'स्प्रे OK' : 'टालें'}
      </span>
    `;
    container.appendChild(card);
  });
}

function renderPast10Days(days) {
  const container = document.getElementById("past-10d-list");
  if (!container) return;

  if (days.length === 0) {
    container.innerHTML = "<div style='color: var(--md-sys-color-outline); padding: 14px;'>इतिहास डेटा उपलब्ध नहीं है।</div>";
    return;
  }

  container.innerHTML = "";
  days.slice().reverse().forEach((d) => {
    const dateObj = new Date(d.date);
    const dateStr = dateObj.toLocaleDateString("hi-IN", { weekday: 'short', month: 'short', day: 'numeric' });

    const row = document.createElement("div");
    row.className = "day-row";
    row.innerHTML = `
      <div class="day-name">${dateStr}</div>
      <div class="day-icon-cond">
        <span style="font-size: 20px;">${d.icon}</span>
        <span>${d.condition_hi}</span>
        ${d.rain_mm > 0 ? `<span style="font-size: 11.5px; color: #1565C0; font-weight: 700; margin-left: 6px;">🌧️ ${d.rain_mm} mm</span>` : '<span style="font-size: 11px; opacity: 0.6; margin-left: 6px;">सूखा (0 mm)</span>'}
      </div>
      <div class="day-temp-bar-container">
        <span style="opacity: 0.65; font-size: 13px;">${Math.round(d.min_temp)}°</span>
        <span style="opacity: 0.4;">/</span>
        <span style="font-weight: 800; font-size: 14px;">${Math.round(d.max_temp)}°</span>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderAgriIntelligence(intel) {
  if (!intel) return;

  if (intel.past_10_days_rain_total_mm !== undefined) {
    document.getElementById("intel-rain-10d").innerText = `${intel.past_10_days_rain_total_mm} mm`;
  }
  if (intel.soil_moisture_status) {
    document.getElementById("intel-soil-status").innerText = `मृदा नमी स्थिति: ${intel.soil_moisture_status}`;
  }
  if (intel.gdd_accumulated_10d !== undefined) {
    document.getElementById("intel-gdd").innerText = `${intel.gdd_accumulated_10d} GDD`;
  }
  if (intel.fungal_disease_risk) {
    const fEl = document.getElementById("intel-fungal-risk");
    fEl.innerText = intel.fungal_disease_risk;
    const card = document.getElementById("intel-fungal-card");
    if (intel.fungal_disease_risk.includes("High")) {
      card.className = "intel-card alert";
      document.getElementById("intel-fungal-desc").innerText = "⚠️ पिछले दिनों में लगातार उच्च आर्द्रता व अनुकूल तापमान रहा है। फफूंदनाशक से फसलों का तुरंत निरीक्षण करें।";
    } else {
      card.className = "intel-card";
      document.getElementById("intel-fungal-desc").innerText = "✓ वातावरण सूखा अथवा सामान्य है। फफूंद जनित रोगों का तात्कालिक खतरा कम है।";
    }
  }
  if (intel.recommended_spray_window) {
    document.getElementById("intel-spray-window").innerText = intel.recommended_spray_window;
  }
}

function switchTab(tabName) {
  const tabs = ['forecast', 'hourly', 'past10', 'intel'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    const view = document.getElementById(`view-${t}`);
    if (t === tabName) {
      if (btn) btn.classList.add("active");
      if (view) view.style.display = "block";
    } else {
      if (btn) btn.classList.remove("active");
      if (view) view.style.display = "none";
    }
  });
}

function switchLocation(lat, lon, name, btn) {
  document.querySelectorAll(".m3-chip").forEach(c => c.classList.remove("active"));
  if (btn) btn.classList.add("active");

  currentLat = lat;
  currentLon = lon;
  currentLocName = name;
  loadWeatherData(lat, lon, name);
}

function fetchLocationGPS() {
  if (!navigator.geolocation) {
    alert("आपके ब्राउज़र में जीपीएस लोकेशन समर्थित नहीं है।");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      switchLocation(lat, lon, "वर्तमान स्थान (GPS Location)", null);
    },
    (err) => {
      alert("जीपीएस स्थान प्राप्त नहीं हो सका: " + err.message);
    }
  );
}

function handleApplyWeatherLocation() {
  const stateEl = document.getElementById("weather-state-select");
  const distEl = document.getElementById("weather-district-select");
  const state = stateEl ? stateEl.value : "";
  const dist = distEl ? distEl.value : "";

  if (!state || !dist) {
    alert("कृपया पहले राज्य और जिला चुनें।");
    return;
  }

  if (window.INDIA_LOCATIONS && window.INDIA_LOCATIONS[state] && window.INDIA_LOCATIONS[state][dist]) {
    const loc = window.INDIA_LOCATIONS[state][dist];
    switchLocation(loc.lat, loc.lon, loc.name, null);
  }
}

window.addEventListener("agrigo:langchange", () => {
  if (window.AgriI18n && window.AgriI18n.applyTranslation) {
    window.AgriI18n.applyTranslation();
  }
});
