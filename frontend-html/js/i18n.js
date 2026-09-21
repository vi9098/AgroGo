/**
 * AgriGo Comprehensive Bilingual Translation Engine (Hindi <-> English)
 * Seamless, non-destructive, bidirectional translation for:
 * - Navigation taskbar & headers
 * - Weather Hub metrics & agro-advisories
 * - Mandi Live Rates & Income Calculator
 * - Farmer AI Chat, voice prompts, and sidebar
 * - Reminders & Task manager
 * - Login & Registration forms
 * 
 * Persists user preference across all pages via localStorage and cookies.
 */

(function () {
  const STORAGE_KEY = "agrigo_lang";
  const DEFAULT_LANG = "hi";

  // Comprehensive Translation Dictionary (Hindi -> English)
  const DICT = {
    // ── Brand & Universal Navigation ──
    "AgriGo": "AgriGo",
    "भारत का कृषि AI मंच • AI 2026": "India's Agri AI Platform • AI 2026",
    "होम (Home)": "Home",
    "होम": "Home",
    "किसान AI चैट": "Farmer AI Chat",
    "पंजीकरण (Register)": "Register",
    "पंजीकरण": "Register",
    "अनुस्मारक": "Reminders",
    "मौसम केंद्र": "Weather Center",
    "मंडी भाव": "Mandi Prices",
    "एडमिन": "Admin",
    "लॉगआउट": "Logout",
    "लॉगिन": "Login",
    "लॉगिन करें": "Login",
    "🌾 किसान लॉगिन": "🌾 Farmer Login",
    "किसान लॉगिन": "Farmer Login",
    "एडमिन लॉगिन": "Admin Login",
    "📡 data.gov.in Agmarknet": "📡 data.gov.in Agmarknet",
    "भाषा चुनें": "Select Language",
    "मौसम": "Weather",
    "अपडेटेड": "Updated",
    "अंतिम सिंक: आज का सत्यापित Agmarknet रिकॉर्ड": "Last sync: Today's verified Agmarknet record",

    // ── Notifications ──
    "कृषि कार्य सूचनाएं": "Agri Task Notifications",
    "0 कार्य लंबित": "0 tasks pending",
    "कोई लंबित अनुस्मारक नहीं है।": "No pending reminders.",
    "📲 ब्राउज़र अलर्ट सक्षम करें": "📲 Enable Browser Alerts",
    "सभी देखें ➔": "View All ➔",
    "✓ पूर्ण करें": "✓ Complete",
    "अतिदेय": "Overdue",
    "आज ही देय": "Due Today",
    "दिन शेष": "days remaining",

    // ── Home Page / Hero ──
    "भारत का सबसे उन्नत AI कृषि साथी": "India's Most Advanced AI Agri Companion",
    "फसल, मौसम, मंडी भाव और सरकारी सलाह — सब कुछ एक ही मंच पर": "Crops, Weather, Mandi Prices & Govt Advisory — All in One Platform",
    "🌾 किसान साथी से बात करें ➔": "🌾 Talk to Farmer AI ➔",
    "💰 ताजा मंडी भाव देखें": "💰 View Live Mandi Rates",
    "🌤️ मौसम पूर्वानुमान": "🌤️ Weather Forecast",
    "⏰ कार्य अनुस्मारक": "⏰ Task Reminders",
    "कृषि मंत्रालय व ICAR के डेटा पर प्रशिक्षित": "Trained on Ministry of Agriculture & ICAR Data",
    "4.5 लाख+ सरकारी उत्पादन व मंडी रिकॉर्ड्स": "4.5 Lakh+ Govt Production & Mandi Records",
    "50,000+ मिट्टी व जलवायु डेटा बिंदु": "50,000+ Soil & Climate Data Points",
    "सत्यापित वैज्ञानिक अनुसंधान": "Verified Scientific Research",
    "त्वरित किसान सेवाएं": "Instant Farmer Services",
    "🌾 AI फसल डॉक्टर व सलाहकार": "🌾 AI Crop Doctor & Advisor",
    "फसल की पत्ती की फोटो भेजें या बोलकर पूछें — सटीक रोग पहचान व जैविक/रासायनिक उपचार तुरंत।": "Upload leaf photo or ask by voice — instant disease diagnosis and treatment.",
    "🌤️ हाइपरलोकल मौसम केंद्र": "🌤️ Hyperlocal Weather Center",
    "अगले 7 दिनों का सटीक मौसम, वर्षा की संभावना व सर्वोत्तम छिड़काव समय (Agromet Advisory)।": "Accurate 7-day forecast, rain probability & best spray window (Agromet Advisory).",
    "💰 दैनिक मंडी भाव व आय कैलकुलेटर": "💰 Daily Mandi Prices & Revenue Calculator",
    "देश भर की प्रमुख मंडियों के लाइव भाव, MSP तुलना व अपनी फसल का शुद्ध मुनाफा जांचें।": "Live mandi rates across India, MSP comparison & calculate your net profit.",
    "⏰ स्मार्ट कृषि अनुस्मारक": "⏰ Smart Agri Reminders",
    "बुवाई, खाद, सिंचाई और कटाई के समय पर स्वचालित WhatsApp व ब्राउज़र अलर्ट्स पाएं।": "Automated reminders for sowing, fertilizer, irrigation & harvest.",

    // ── Mandi Prices & Revenue Calculator ──
    "भारत सरकार लाइव मंडी भाव व फसल आय कैलकुलेटर (Agmarknet)": "Govt of India Live Mandi Rates & Crop Revenue Calculator (Agmarknet)",
    "💰 ताजा दैनिक मंडी भाव व फसल आय कैलकुलेटर": "💰 Daily Mandi Prices & Crop Revenue Calculator",
    "भारत भर की प्रमुख APMC मंडियों के आधिकारिक मॉडल, न्यूनतम व अधिकतम भाव। अपनी फसल की आय, लागत और MSP से तुलना देखें।": "Official modal, min & max rates from APMC mandis across India. Compare crop revenue, costs & MSP.",
    "📊 फसल आय व मुनाफा कैलकुलेटर": "📊 Crop Revenue & Profit Calculator",
    "लाइव मंडी दर × आपकी पैदावार = अनुमानित सकल आय, लागत व शुद्ध मुनाफा": "Live Mandi Rate × Your Yield = Estimated Gross Revenue, Cost & Net Profit",
    "फसल का नाम (Crop)": "Crop Name",
    "कुल रकबा (Acres)": "Total Area (Acres)",
    "पैदावार (क्विं/एकड़)": "Yield (Qtl/Acre)",
    "राज्य (वैकल्पिक)": "State (Optional)",
    "संपूर्ण भारत": "All India",
    "संपूर्ण भारत (सभी राज्य)": "All India (All States)",
    "सभी राज्य": "All States",
    "गणना करें ➔": "Calculate ➔",
    "कुल पैदावार": "Total Production",
    "मंडी मॉडल भाव": "Mandi Modal Rate",
    "सकल बाजार मूल्य": "Gross Market Revenue",
    "अनुमानित लागत": "Estimated Cost",
    "ICAR लागत": "Estimated Cost",
    "शुद्ध किसान लाभ": "Net Farmer Profit",
    "सरकारी MSP": "Govt MSP",
    "ओपन मार्केट भाव": "Open Market Rate",
    "श्रेष्ठ मंडी": "Best Mandi",
    "उपलब्ध मंडी औसत दर": "Available Mandi Average Rate",
    "राष्ट्रीय औसत APMC मॉडल भाव": "National Average APMC Modal Rate",
    "अनुमानित आय विवरण": "Estimated Revenue Breakdown",
    "अमान्य फसल का नाम (Invalid Crop Name)": "Invalid Crop Name",
    "कृपया सही फसल का नाम लिखें ताकि सही परिणाम मिल सके (उदा. गेहूं, धान, सरसों, चना, मक्का, टमाटर, आलू, प्याज आदि)।": "Please enter a valid crop name to get accurate results (e.g. Wheat, Paddy, Mustard, Gram, Maize, Tomato, Potato, Onion, etc.).",
    "फसल का नाम खाली है (Crop Name Required)": "Crop Name Required",
    "कृपया फसल का नाम दर्ज करें (उदा. गेहूं, धान, सरसों, चना, मक्का आदि)।": "Please enter crop name (e.g. Wheat, Paddy, Mustard, Gram, Maize, etc.).",
    "रिकॉर्ड्स उपलब्ध": "Records Available",
    "86+ जिंसें · 12+ राज्य": "86+ Commodities · All States",
    "सरकारी डेटा रीफ्रेश करें": "Refresh Govt Data",
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
    "‹ पिछला": "‹ Previous",
    "अगला ›": "Next ›",
    "फिल्टर रीसेट": "Reset Filters",
    "🔍 जिंस या मंडी खोजें...": "🔍 Search commodity or mandi...",
    "मंडी भाव लोड हो रहे हैं...": "Loading mandi rates...",

    // ── Crop Chips ──
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

    // ── Weather Center ──
    "🌤️ मौसम केंद्र": "🌤️ Weather Center",
    "वर्तमान मौसम": "Current Weather",
    "तापमान": "Temperature",
    "महसूस होता है": "Feels Like",
    "नमी": "Humidity",
    "हवा की गति": "Wind Speed",
    "बारिश की संभावना": "Rain Probability",
    "7 दिवसीय पूर्वानुमान": "7-Day Forecast",
    "24 घंटे का पूर्वानुमान": "24-Hour Forecast",
    "विस्तृत कृषि मौसम स्थिति": "Detailed Agro-Weather Conditions",
    "कृषि परामर्श बुलेटिन": "Agro Advisory Bulletin",
    "मौसम डेटा लोड हो रहा है...": "Loading weather data...",
    "सुरक्षित ✓ (हवा अनुकूल)": "Safe ✓ (Wind Favorable)",
    "असुरक्षित ⚠️ (हवा/बारिश)": "Unsafe ⚠️ (Wind/Rain Risk)",
    "सुरक्षित ✓ (हवा सामान्य)": "Safe ✓ (Normal Wind)",
    "असुरक्षित ⚠️ (छिड़काव टालें)": "Unsafe ⚠️ (Postpone Spray)",
    "सिंचाई अनुकूल ✓": "Irrigation Advisable ✓",
    "सिंचाई टालें 🌧️ (बारिश की संभावना)": "Postpone Irrigation 🌧️ (Rain Expected)",
    "सर्वश्रेष्ठ छिड़काव समय": "Best Spray Window",
    "सर्वश्रेष्ठ छिड़काव समय (Best Spray Window)": "Best Spray Window",
    "सत्यापित मौसम स्रोत: Open-Meteo API व भारत मौसम विज्ञान विभाग (IMD Agromet Advisory Service)।": "Verified Weather Sources: Open-Meteo API & IMD Agromet Advisory Service.",

    // ── Farmer AI Portal & Chat ──
    "AgriGo AI कृषि मित्र": "AgriGo AI Farm Companion",
    "🟢 सक्रिय | ICAR + TNAU + FAO | 455k+ रिकॉर्ड्स प्रशिक्षित": "🟢 Active | ICAR + TNAU + FAO | 455k+ Trained Records",
    "खेत व मिट्टी स्थिति": "Farm & Soil Status",
    "सक्रिय फसल चक्र": "Active Crop Cycles",
    "ताजा मंडी भाव": "Latest Mandi Rates",
    "शीघ्र सलाह": "Quick Advisory",
    "🌱 कौन सी फसल बोएं?": "🌱 Which Crop to Sow?",
    "📈 पैदावार अनुमान": "📈 Yield Estimate",
    "🟡 सरसों की खेती": "🟡 Mustard Farming",
    "💧 आज सिंचाई?": "💧 Irrigate Today?",
    "🍅 टमाटर रोग": "🍅 Tomato Disease",
    "🌾 धान खेती": "🌾 Paddy Farming",
    "बोलकर पूछें": "Speak by Mic",
    "पत्ती की फोटो": "Leaf Photo",
    "भेजें ➔": "Send ➔",
    "🔊 बोलकर सुनाएं": "🔊 Speak Aloud",
    "सत्यापित स्रोत": "Verified Source",
    "🏛️ सत्यापित स्रोत": "🏛️ Verified Sources",

    // ── Reminders Dashboard ──
    "कृषि अनुस्मारक": "Agri Reminders",
    "लंबित कार्य": "Pending Tasks",
    "पूर्ण कार्य": "Completed Tasks",
    "सभी कार्य": "All Tasks",
    "नया अनुस्मारक जोड़ें": "Add New Reminder",
    "कार्य का विवरण": "Task Description",
    "नियत तारीख": "Due Date",
    "प्राथमिकता": "Priority",
    "अति-आवश्यक": "Urgent",
    "सामान्य": "Normal",
    "कम": "Low",
    "सुरक्षित करें": "Save Reminder",
    "रद्द करें": "Cancel",
    "कार्य जोड़ें": "Add Task",

    // ── Registration & Login ──
    "नया किसान पंजीकरण": "New Farmer Registration",
    "पूरा नाम": "Full Name",
    "मोबाइल नंबर": "Mobile Number",
    "पासवर्ड": "Password",
    "गांव / कस्बा": "Village / Town",
    "फार्म का आकार (एकड़)": "Farm Size (Acres)",
    "पंजीकरण करें": "Register Now",
    "पहले से खाता है? लॉगिन करें": "Already have an account? Login",
    "खाता नहीं है? नया पंजीकरण करें": "Don't have an account? Register Now",
    "-- राज्य चुनें --": "-- Select State --",
    "-- जिला चुनें --": "-- Select District --",
    "-- राज्य चुनें (Select State) --": "-- Select State --",
    "-- जिला चुनें (Select District) --": "-- Select District --"
  };

  // Build Reverse Dictionary (English -> Hindi)
  const REVERSE_DICT = {};
  for (const [hi, en] of Object.entries(DICT)) {
    const enTrim = en.trim();
    if (!REVERSE_DICT[enTrim]) {
      REVERSE_DICT[enTrim] = hi.trim();
    }
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
    // Normalize: 'hi' is Hindi, 'en' is English; 'ta','te','pa' map cleanly to English mode for UI text
    const normalized = (lang === "hi") ? "hi" : "en";

    try {
      localStorage.setItem(STORAGE_KEY, lang);
      document.cookie = `${STORAGE_KEY}=${encodeURIComponent(lang)}; path=/; max-age=31536000; SameSite=Lax`;
    } catch (_) {}

    document.documentElement.lang = normalized;

    // Sync header dropdown
    const hdrSel = document.getElementById("hdr-lang-select");
    if (hdrSel && hdrSel.value !== lang) {
      hdrSel.value = lang;
    }

    // Sync farmer chat dropdown
    const chatSel = document.getElementById("chat-lang-select");
    if (chatSel && chatSel.value !== lang) {
      chatSel.value = lang;
    }

    applyTranslation(normalized);

    // Notify listeners across app (e.g. mandi.js, farmer.js, weather.js)
    try {
      window.dispatchEvent(new CustomEvent("agrigo:langchange", { detail: { lang: normalized, rawLang: lang } }));
    } catch (_) {}
  }

  /**
   * Non-destructive, node-level translation.
   * Preserves child elements, icons, badges, and event listeners.
   */
  function applyTranslation(targetLang, rootNode = document.body) {
    if (!rootNode) return;
    const isHindi = (targetLang === "hi");
    const dict = isHindi ? REVERSE_DICT : DICT;

    // 1. Explicit data-i18n elements
    rootNode.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (isHindi) {
        el.textContent = el.getAttribute("data-orig-text") || key;
      } else {
        if (!el.getAttribute("data-orig-text")) {
          el.setAttribute("data-orig-text", el.textContent.trim());
        }
        if (DICT[key]) el.textContent = DICT[key];
      }
    });

    // 2. Safe Text Node Walker: replaces text without destroying DOM children or event handlers
    const walker = document.createTreeWalker(
      rootNode,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function (node) {
          if (!node || !node.nodeValue) return NodeFilter.FILTER_REJECT;
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          const tag = parent.tagName;
          if (["SCRIPT", "STYLE", "NOSCRIPT", "CODE", "PRE"].includes(tag)) {
            return NodeFilter.FILTER_REJECT;
          }
          if (parent.hasAttribute("data-no-translate")) {
            return NodeFilter.FILTER_REJECT;
          }
          const val = node.nodeValue.trim();
          if (!val || val.length < 2) return NodeFilter.FILTER_SKIP;
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    const nodesToTranslate = [];
    while (walker.nextNode()) {
      nodesToTranslate.push(walker.currentNode);
    }

    nodesToTranslate.forEach(node => {
      const currentVal = node.nodeValue.trim();
      if (!currentVal) return;

      // Cache original Hindi text on node
      if (!node._origAgriText) {
        node._origAgriText = currentVal;
      }

      if (isHindi) {
        // Restore cached original text if available
        if (node._origAgriText && DICT[node._origAgriText]) {
          const leadWs = node.nodeValue.match(/^\s*/)[0];
          const trailWs = node.nodeValue.match(/\s*$/)[0];
          node.nodeValue = leadWs + node._origAgriText + trailWs;
        } else if (REVERSE_DICT[currentVal]) {
          const leadWs = node.nodeValue.match(/^\s*/)[0];
          const trailWs = node.nodeValue.match(/\s*$/)[0];
          node.nodeValue = leadWs + REVERSE_DICT[currentVal] + trailWs;
        }
      } else {
        // Translate to English
        const lookup = node._origAgriText || currentVal;
        if (DICT[lookup]) {
          const leadWs = node.nodeValue.match(/^\s*/)[0];
          const trailWs = node.nodeValue.match(/\s*$/)[0];
          node.nodeValue = leadWs + DICT[lookup] + trailWs;
        } else {
          // Check substring replacements for compound sentences
          for (const [hiStr, enStr] of Object.entries(DICT)) {
            if (hiStr.length >= 4 && node.nodeValue.includes(hiStr)) {
              node.nodeValue = node.nodeValue.replace(hiStr, enStr);
            }
          }
        }
      }
    });

    // 3. Translate Placeholders
    rootNode.querySelectorAll("input[placeholder], textarea[placeholder]").forEach(input => {
      const ph = input.getAttribute("placeholder");
      if (!ph) return;

      if (!input.dataset.origPlaceholder) {
        input.dataset.origPlaceholder = ph;
      }

      if (isHindi) {
        input.setAttribute("placeholder", input.dataset.origPlaceholder);
      } else {
        const orig = input.dataset.origPlaceholder;
        if (DICT[orig]) {
          input.setAttribute("placeholder", DICT[orig]);
        } else {
          for (const [hiStr, enStr] of Object.entries(DICT)) {
            if (hiStr.length >= 4 && ph.includes(hiStr)) {
              input.setAttribute("placeholder", ph.replace(hiStr, enStr));
              break;
            }
          }
        }
      }
    });

    // 4. Translate Select Options (State, District, Dropdowns)
    rootNode.querySelectorAll("select option").forEach(opt => {
      const text = opt.textContent.trim();
      if (!opt.dataset.origText) {
        opt.dataset.origText = text;
      }
      if (isHindi) {
        opt.textContent = opt.dataset.origText;
      } else {
        const orig = opt.dataset.origText;
        if (DICT[orig]) {
          opt.textContent = DICT[orig];
        }
      }
    });
  }

  function init() {
    const current = getLanguage();
    setLanguage(current);

    // Bind header select
    const hdrSel = document.getElementById("hdr-lang-select");
    if (hdrSel) {
      hdrSel.value = current;
      hdrSel.addEventListener("change", (e) => {
        setLanguage(e.target.value);
      });
    }

    // Bind chat select
    const chatSel = document.getElementById("chat-lang-select");
    if (chatSel) {
      chatSel.value = current;
      chatSel.addEventListener("change", (e) => {
        setLanguage(e.target.value);
      });
    }
  }

  // Fast boot: run on DOM ready or immediately if already loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Pageshow event for back-forward cache consistency
  window.addEventListener("pageshow", () => {
    applyTranslation(getLanguage() === "hi" ? "hi" : "en");
  });

  // Global Export
  window.AgriI18n = {
    getLanguage,
    setLanguage,
    applyTranslation: (node) => applyTranslation(getLanguage() === "hi" ? "hi" : "en", node || document.body),
    t: (key) => {
      const lang = getLanguage();
      if (lang === "hi") return key;
      return DICT[key] || key;
    }
  };
})();
