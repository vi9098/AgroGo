/**
 * AgriGo Automatic Site-wide Bilingual Translation Engine (Hindi <-> English)
 * Dynamically translates navigation, taskbar, cards, headers, buttons, tables, and forms.
 * Persists user preference across pages in localStorage and cookies.
 */

(function () {
  const STORAGE_KEY = "agrigo_lang";
  const DEFAULT_LANG = "hi";

  // Comprehensive Translation Dictionary
  const TRANSLATIONS = {
    // Brand & Navigation
    "भारत का कृषि AI मंच • AI 2026": "India's Agri AI Platform • AI 2026",
    "होम (Home)": "Home",
    "किसान AI चैट": "Farmer AI Chat",
    "पंजीकरण (Register)": "Register",
    "अनुस्मारक": "Reminders",
    "मौसम केंद्र": "Weather Center",
    "मंडी भाव": "Mandi Prices",
    "एडमिन": "Admin",
    "🌾 किसान लॉगिन": "🌾 Farmer Login",
    "लॉगआउट": "Logout",
    "मौसम लोड हो रहा है...": "Loading weather...",
    "मंडी भाव लोड हो रहे हैं...": "Loading mandi rates...",
    "🔔 कृषि कार्य सूचनाएं": "🔔 Agri Task Notifications",
    "कोई लंबित अनुस्मारक नहीं है।": "No pending reminders.",
    "📲 ब्राउज़र अलर्ट सक्षम करें": "📲 Enable Browser Alerts",
    "सभी देखें ➔": "View All ➔",
    "0 कार्य लंबित": "0 tasks pending",

    // Common Buttons & Actions
    "गणना करें ➔": "Calculate ➔",
    "सरकारी डेटा रीफ्रेश करें": "Refresh Govt Data",
    "अंतिम सिंक: आज का सत्यापित Agmarknet रिकॉर्ड": "Last sync: Today's verified Agmarknet record",
    "रिकॉर्ड्स उपलब्ध": "Records Available",
    "86+ जिंसें · 12+ राज्य": "86+ Commodities · All States",
    "भेजें ➔": "Send ➔",
    "📈 पैदावार": "📈 Yield",
    "🌱 श्रेष्ठ फसल": "🌱 Best Crop",
    "💬 AI से संपूर्ण पैकेज पूछें ➔": "💬 Ask AI Complete Advisory ➔",
    "🎙️ बोलकर पूछें": "🎙️ Speak to Ask",
    "📷 रोग पहचानें": "📷 Disease Diagnose",
    "⏰ अनुस्मारक डैशबोर्ड ➔": "⏰ Reminders Dashboard ➔",
    "📊 AI पैदावार कैलकुलेटर": "📊 AI Yield Calculator",
    "कृषि मंत्रालय के 4.5 लाख+ रिकॉर्ड्स पर प्रशिक्षित AI।": "AI trained on 4.5 lakh+ Ministry of Agriculture records.",

    // Mandi & Income Calculator
    "💰 ताजा दैनिक मंडी भाव व फसल आय कैलकुलेटर": "💰 Daily Mandi Prices & Crop Income Calculator",
    "भारत भर की प्रमुख APMC मंडियों के आधिकारिक मॉडल, न्यूनतम व अधिकतम भाव। अपनी फसल की आय, लागत और MSP से तुलना देखें।": "Official modal, min and max prices from major APMC mandis across India. View your crop revenue, cost and MSP comparison.",
    "📊 फसल आय व मुनाफा कैलकुलेटर": "📊 Crop Revenue & Profit Calculator",
    "लाइव मंडी दर × आपकी पैदावार = अनुमानित सकल आय, लागत व शुद्ध मुनाफा": "Live Mandi Rate × Your Yield = Estimated Gross Revenue, Cost & Net Profit",
    "फसल का नाम (Crop)": "Crop Name",
    "कुल रकबा (Acres)": "Total Area (Acres)",
    "पैदावार (क्विं/एकड़ा)": "Yield (Qtl/Acre)",
    "पैदावार (क्विं/एकड़)": "Yield (Qtl/Acre)",
    "राज्य (वैकल्पिक)": "State (Optional)",
    "संपूर्ण भारत": "All India",
    "संपूर्ण भारत (सभी राज्य)": "All India (All States)",
    "सभी राज्य (All States)": "All States",
    "कुल पैदावार": "Total Production",
    "मंडी मॉडल भाव": "Mandi Modal Rate",
    "सकल बाजार मूल्य": "Gross Market Revenue",
    "ICAR लागत": "Estimated Cost",
    "शुद्ध किसान लाभ": "Net Farmer Profit",
    "ओपन मार्केट भाव": "Open Market Rate",
    "सरकारी MSP": "Govt MSP",
    "श्रेष्ठ मंडी:": "Best Mandi:",
    "*Agmarknet मॉडल दरों व ICAR लागत पर आधारित": "*Based on Agmarknet modal rates & ICAR benchmark costs",
    "🔍 जिंस या मंडी खोजें...": "🔍 Search commodity or mandi...",
    "फिल्टर रीसेट": "Reset Filters",

    // Quick Crop Chips
    "🌾 गेहूं": "🌾 Wheat",
    "🍚 धान": "🍚 Paddy",
    "🟡 सरसों": "🟡 Mustard",
    "🟤 चना": "🟤 Chickpea",
    "🌽 मक्का": "🌽 Maize",
    "🌱 सोयाबीन": "🌱 Soybean",
    "⚪ कपास": "⚪ Cotton",
    "🍅 टमाटर": "🍅 Tomato",
    "🥔 आलू": "🥔 Potato",
    "🧅 प्याज": "🧅 Onion",

    // Mandi Table Headers
    "फसल / जिंस": "Crop / Commodity",
    "राज्य": "State",
    "जिला": "District",
    "मंडी": "Mandi",
    "किस्म": "Variety",
    "मॉडल भाव (₹/क्विं)": "Modal Rate (₹/Qtl)",
    "MSP स्थिति": "MSP Status",
    "न्यूनतम भाव": "Min Price",
    "अधिकतम भाव": "Max Price",
    "आगमन तिथि": "Arrival Date",
    "पिछला": "Previous",
    "अगला": "Next",

    // Weather Hub
    "🌤️ मौसम केंद्र": "🌤️ Weather Center",
    "वर्तमान मौसम": "Current Weather",
    "तापमान": "Temperature",
    "महसूस होता है": "Feels Like",
    "नमी": "Humidity",
    "हवा की गति": "Wind Speed",
    "बारिश की संभावना": "Rain Probability",
    "7 दिवसीय पूर्वानुमान": "7-Day Forecast",
    "कृषि मौसम सलाह": "Agro-Weather Advisory",
    "विस्तृत कृषि मौसम स्थिति": "Detailed Agro-Weather Conditions",
    "कृषि परामर्श बुलेटिन": "Agro Advisory Bulletin",
    "मौसम डेटा लोड हो रहा है...": "Loading weather data...",

    // Reminders
    "कृषि अनुस्मारक": "Agri Reminders",
    "लंबित कार्य": "Pending Tasks",
    "पूर्ण कार्य": "Completed Tasks",
    "नया अनुस्मारक जोड़ें": "Add New Reminder",
    "कार्य का विवरण": "Task Description",
    "नियत तारीख": "Due Date",
    "प्राथमिकता": "Priority",

    // Registration & Login
    "नया किसान पंजीकरण": "New Farmer Registration",
    "पूरा नाम": "Full Name",
    "मोबाइल नंबर": "Mobile Number",
    "पासवर्ड": "Password",
    "गांव / कस्बा": "Village / Town",
    "फार्म का आकार (एकड़)": "Farm Size (Acres)",
    "पंजीकरण करें": "Register Now",
    "पहले से खाता है? लॉगिन करें": "Already have an account? Login",
    "किसान लॉगिन": "Farmer Login",
    "खाता नहीं है? नया पंजीकरण करें": "Don't have an account? Register Now",
    "लॉगिन करें": "Login",
    "-- राज्य चुनें (Select State) --": "-- Select State --",
    "-- जिला चुनें (Select District) --": "-- Select District --"
  };

  // Build reverse map (English -> Hindi)
  const REVERSE_TRANSLATIONS = {};
  for (const [hi, en] of Object.entries(TRANSLATIONS)) {
    REVERSE_TRANSLATIONS[en.trim()] = hi.trim();
  }

  function getLanguage() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return stored;
    } catch (_) {}
    return DEFAULT_LANG;
  }

  function setLanguage(lang) {
    if (!lang) lang = DEFAULT_LANG;
    // Normalize: treat 'hi' as Hindi, everything else ('en', 'ta', 'te', 'pa') as English/target
    const normalized = (lang === "hi") ? "hi" : "en";

    try {
      localStorage.setItem(STORAGE_KEY, normalized);
      document.cookie = `${STORAGE_KEY}=${normalized}; path=/; max-age=31536000;`;
    } catch (_) {}

    document.documentElement.lang = normalized;

    // Sync select dropdowns
    const hdrSel = document.getElementById("hdr-lang-select");
    if (hdrSel && hdrSel.value !== normalized) {
      hdrSel.value = normalized;
    }
    const chatSel = document.getElementById("chat-lang-select");
    if (chatSel && chatSel.value !== normalized) {
      chatSel.value = normalized;
    }

    applyTranslation(normalized);
  }

  function applyTranslation(lang) {
    const isHindi = (lang === "hi");
    const sourceMap = isHindi ? REVERSE_TRANSLATIONS : TRANSLATIONS;

    // 1. Elements with data-i18n attribute
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (isHindi && key) {
        el.textContent = key;
      } else if (!isHindi && TRANSLATIONS[key]) {
        el.textContent = TRANSLATIONS[key];
      }
    });

    // 2. Translate Taskbar Links
    document.querySelectorAll(".taskbar .task-link, .nav-links a").forEach(link => {
      const txt = link.textContent.trim();
      for (const [src, dst] of Object.entries(sourceMap)) {
        if (txt.includes(src)) {
          link.innerHTML = link.innerHTML.replace(src, dst);
          break;
        }
      }
    });

    // 3. Translate Specific UI Elements & Buttons
    const textSelectors = [
      "h1", "h2", "h3", "h4",
      ".section-title", ".section-sub", ".sidebar-head",
      ".btn", ".metric-lbl", ".crop-chip", "label.form-label",
      "th", ".badge", "#sync-status", "#calc-disclaimer",
      ".brand-tagline", "#hdr-kisan-login-btn"
    ];

    document.querySelectorAll(textSelectors.join(",")).forEach(el => {
      // Don't translate inputs, selects, or scripts
      if (["INPUT", "SELECT", "TEXTAREA", "SCRIPT", "STYLE"].includes(el.tagName)) return;
      if (el.children.length > 2) return; // Skip complex containers

      const raw = el.textContent.trim();
      if (!raw) return;

      if (sourceMap[raw]) {
        el.textContent = sourceMap[raw];
        return;
      }

      // Substring replacements for composite labels
      for (const [src, dst] of Object.entries(sourceMap)) {
        if (src.length > 3 && raw.includes(src)) {
          el.innerHTML = el.innerHTML.replace(src, dst);
          break;
        }
      }
    });

    // 4. Translate Input Placeholders
    document.querySelectorAll("input[placeholder], textarea[placeholder]").forEach(input => {
      const ph = input.getAttribute("placeholder");
      if (!ph) return;
      if (sourceMap[ph]) {
        input.setAttribute("placeholder", sourceMap[ph]);
      } else {
        for (const [src, dst] of Object.entries(sourceMap)) {
          if (ph.includes(src)) {
            input.setAttribute("placeholder", ph.replace(src, dst));
            break;
          }
        }
      }
    });
  }

  function init() {
    const current = getLanguage();
    setLanguage(current);

    // Attach listener to header select
    const hdrSel = document.getElementById("hdr-lang-select");
    if (hdrSel) {
      hdrSel.value = (current === "hi") ? "hi" : "en";
      hdrSel.addEventListener("change", (e) => {
        setLanguage(e.target.value);
      });
    }

    // Attach listener to chat select if present
    const chatSel = document.getElementById("chat-lang-select");
    if (chatSel) {
      chatSel.value = (current === "hi") ? "hi" : "en";
      chatSel.addEventListener("change", (e) => {
        setLanguage(e.target.value);
      });
    }
  }

  // Run on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Also re-apply translation when pageshow fires or dynamic content loads
  window.addEventListener("pageshow", () => {
    applyTranslation(getLanguage());
  });

  // Global Export
  window.AgriI18n = {
    getLanguage,
    setLanguage,
    applyTranslation: () => applyTranslation(getLanguage()),
    t: (key) => {
      const lang = getLanguage();
      if (lang === "hi") return key;
      return TRANSLATIONS[key] || key;
    }
  };
})();
