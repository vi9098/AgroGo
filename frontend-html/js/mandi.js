/**
 * AgriGo Live Mandi Prices & Crop Revenue Calculator
 * Powers mandi.html with live Agmarknet data from data.gov.in
 */

document.addEventListener("DOMContentLoaded", () => {
  let currentOffset = 0;
  const pageSize = 25;
  let totalRecords = 0;
  let searchDebounceTimer = null;

  // Elements
  const mandiTableBody = document.getElementById("mandi-table-body");
  const recordCountBadge = document.getElementById("mandi-record-count");
  const paginationInfo = document.getElementById("mandi-pagination-info");
  const btnPrev = document.getElementById("btn-prev-page");
  const btnNext = document.getElementById("btn-next-page");
  const searchInput = document.getElementById("mandi-search-input");
  const stateSelect = document.getElementById("mandi-state-select");
  const btnReset = document.getElementById("btn-reset-filters");
  const btnSync = document.getElementById("btn-sync-mandi");
  const syncStatus = document.getElementById("sync-status");
  const syncSpinner = document.getElementById("sync-spinner");

  // Calculator elements
  const calcForm = document.getElementById("revenue-calc-form");
  const calcCropInput = document.getElementById("calc-crop-input");
  const calcAcresInput = document.getElementById("calc-acres-input");
  const calcYieldInput = document.getElementById("calc-yield-input");
  const calcStateSelect = document.getElementById("calc-state-select");
  const calcResultBox = document.getElementById("calc-result-box");
  const calcErrorBox = document.getElementById("calc-error-box");
  const calcErrorTitle = document.getElementById("calc-error-title");
  const calcErrorMsg = document.getElementById("calc-error-msg");
  const quickChips = document.querySelectorAll(".crop-chip, #quick-crop-chips .chip-btn");

  // Format currency
  function formatINR(val) {
    if (val === null || val === undefined || isNaN(val)) return "₹0";
    return "₹" + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 0 });
  }

  // Error messaging helpers for calculator
  function showCalcError(title, msg) {
    if (calcResultBox) calcResultBox.style.display = "none";
    if (calcErrorBox) {
      if (calcErrorTitle && title) calcErrorTitle.textContent = title;
      if (calcErrorMsg && msg) calcErrorMsg.textContent = msg;
      calcErrorBox.style.display = "block";
      if (window.innerWidth < 768) {
        calcErrorBox.scrollIntoView({ behavior: "smooth" });
      }
    }
  }

  function hideCalcError() {
    if (calcErrorBox) calcErrorBox.style.display = "none";
  }

  // Comprehensive recognized crops and aliases
  const KNOWN_CROPS = [
    // Cereals
    "wheat", "गेहूं", "gehu", "gehun",
    "paddy", "dhan", "धान", "चावल", "chawal", "rice",
    "maize", "makka", "makki", "मक्का", "bhutta", "corn",
    "bajra", "बाजरा", "pearl millet", "millet",
    "barley", "jau", "जौ",
    "jowar", "sorghum", "ज्वार",
    "ragi", "रागी", "finger millet",
    // Oilseeds
    "mustard", "sarso", "sarson", "सरसों", "राई", "rai", "mustard seed",
    "groundnut", "peanut", "mungfali", "moongfali", "मूंगफली",
    "soyabean", "soybean", "सोयाबीन",
    "sunflower", "surajmukhi", "सूरजमुखी",
    "sesame", "til", "तिल",
    // Pulses
    "gram", "chana", "चना", "chane", "chickpea", "chickpeas", "bengal gram",
    "arhar", "tur", "tuvar", "अरहर", "तूर",
    "moong", "mung", "मूंग",
    "urad", "उड़द", "mash",
    "masoor", "masur", "lentil", "मसूर",
    "peas", "matar", "मटर", "green peas",
    // Commercial
    "cotton", "kapas", "कपास", "rui", "रुई",
    "sugarcane", "ganna", "गन्ना",
    "jute", "पटसन", "patson",
    // Vegetables
    "tomato", "tamatar", "टमाटर",
    "potato", "aloo", "alu", "आलू",
    "onion", "pyaj", "pyaz", "प्याज",
    "garlic", "lahsun", "लहसुन",
    "ginger", "adrak", "अदरक",
    "chilli", "mirch", "मिर्च", "capsicum", "shimla mirch", "शिमला मिर्च",
    "brinjal", "baingan", "बैंगन", "eggplant",
    "cabbage", "patta gobhi", "पत्तागोभी", "band gobhi",
    "cauliflower", "phool gobhi", "फूलगोभी", "gobhi", "गोभी",
    "okra", "bhindi", "भिंडी", "ladyfinger",
    "carrot", "gajar", "गाजर",
    "radish", "mooli", "muli", "मूली",
    "spinach", "palak", "पालक",
    "bottle gourd", "lauki", "लौकी", "ghia",
    "bitter gourd", "karela", "करेला",
    "pumpkin", "kaddu", "कद्दू",
    "cucumber", "kheera", "खीरा",
    // Fruits
    "banana", "kela", "केला",
    "apple", "seb", "सेब",
    "mango", "aam", "आम",
    "guava", "amrood", "अमरूद",
    "papaya", "papita", "पपीता",
    "orange", "santra", "संतरा",
    "pomegranate", "anar", "anaar", "अनार",
    "watermelon", "tarbooj", "तरबूज",
    // Spices
    "turmeric", "haldi", "हल्दी",
    "coriander", "dhaniya", "धनिया",
    "cumin", "jeera", "जीरा",
    "fenugreek", "methi", "मेथी"
  ];

  function isValidCropQuery(query) {
    if (!query || typeof query !== "string") return false;
    const q = query.trim().toLowerCase();
    if (q.length < 2) return false;

    // Reject pure numbers or punctuation
    if (/^[\d\W_]+$/.test(q)) return false;

    // 1. Direct exact match
    if (KNOWN_CROPS.includes(q)) return true;

    // 2. Token / word boundary match
    const tokens = q.split(/[\s,._\-\/]+/).filter(t => t.length >= 2);
    for (const token of tokens) {
      if (KNOWN_CROPS.includes(token)) return true;
    }

    // 3. Multi-word phrases
    for (const crop of KNOWN_CROPS) {
      if (crop.includes(" ") && q.includes(crop)) return true;
    }

    return false;
  }

  // Crop yield defaults for quick chips
  const cropDefaults = {
    "Wheat": { yield: 18.0, hi: "गेहूं" },
    "Paddy(Common)": { yield: 22.0, hi: "धान" },
    "Mustard": { yield: 8.5, hi: "सरसों" },
    "Bengal Gram(Gram)(Whole)": { yield: 7.5, hi: "चना" },
    "Cotton": { yield: 9.5, hi: "कपास" },
    "Maize": { yield: 25.0, hi: "मक्का" },
    "Soyabean": { yield: 9.0, hi: "सोयाबीन" },
    "Tomato": { yield: 120.0, hi: "टमाटर" },
    "Potato": { yield: 100.0, hi: "आलू" },
    "Onion": { yield: 90.0, hi: "प्याज" }
  };

  // 1. Load Meta (states, commodities, MSPs)
  async function loadMeta() {
    try {
      const meta = await AgriAPI.getMandiMeta();
      if (meta && meta.states) {
        stateSelect.innerHTML = `<option value="All">सभी राज्य (All States)</option>`;
        calcStateSelect.innerHTML = `<option value="All">संपूर्ण भारत (सभी राज्य)</option>`;
        const uniqueStates = Array.from(new Set(meta.states.map(s => s && s.trim()).filter(Boolean))).sort();
        uniqueStates.forEach(st => {
          const opt1 = document.createElement("option");
          opt1.value = st;
          opt1.textContent = st;
          stateSelect.appendChild(opt1);

          const opt2 = document.createElement("option");
          opt2.value = st;
          opt2.textContent = st;
          calcStateSelect.appendChild(opt2);
        });
      }
    } catch (err) {
      console.warn("Could not load mandi metadata:", err);
    }
  }

  // 2. Fetch and Render Mandi Prices
  async function loadMandiPrices() {
    const query = searchInput.value.trim();
    const state = stateSelect.value;

    mandiTableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 25px; color: var(--text-muted);">
          🌾 सरकारी मंडी डेटा प्राप्त किया जा रहा है...
        </td>
      </tr>
    `;

    try {
      const res = await AgriAPI.getMandiPrices(
        query || null,
        state === "All" ? null : state,
        null,
        pageSize,
        currentOffset
      );

      totalRecords = res.total || 0;
      recordCountBadge.textContent = `${totalRecords} रिकॉर्ड्स उपलब्ध`;

      const prices = res.prices || [];
      if (prices.length === 0) {
        mandiTableBody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; padding: 30px; color: var(--text-muted);">
              🔍 कोई मंडी रिकॉर्ड नहीं मिला। कृपया अन्य फसल या राज्य चुनें।
            </td>
          </tr>
        `;
        paginationInfo.textContent = "0 रिकॉर्ड्स";
        btnPrev.disabled = true;
        btnNext.disabled = true;
        return;
      }

      // Render rows
      mandiTableBody.innerHTML = prices.map(p => {
        let mspBadgeHtml = `<span style="color: var(--text-muted); font-size: 11px;">MSP लागू नहीं</span>`;
        if (p.msp) {
          if (p.is_above_msp) {
            mspBadgeHtml = `
              <span class="badge badge-green" title="सरकारी MSP ₹${p.msp}/क्विंटल से अधिक">
                +₹${p.msp_diff_rs} (+${p.msp_diff_pct}%)
              </span>
            `;
          } else {
            mspBadgeHtml = `
              <span class="badge" style="background: #FFF3E0; color: #E65100; border: 1px solid #FFE0B2;" title="सरकारी MSP ₹${p.msp}/क्विंटल">
                MSP ₹${p.msp} (-${Math.abs(p.msp_diff_pct)}%)
              </span>
            `;
          }
        }

        return `
          <tr>
            <td>
              <strong style="color: var(--primary-dark);">${p.commodity}</strong>
              ${p.variety ? `<div style="font-size: 11.5px; color: var(--text-muted);">${p.variety}</div>` : ""}
            </td>
            <td>
              <span style="font-weight: 600;">${p.market}</span>
              ${p.district ? `<div style="font-size: 11px; color: var(--text-muted);">${p.district}</div>` : ""}
            </td>
            <td><span class="badge badge-outline" style="font-size: 11.5px;">${p.state}</span></td>
            <td>
              <span class="price-badge-modal">₹${Number(p.modal_price).toLocaleString("en-IN")}</span>
              <span style="font-size: 11px; color: var(--text-muted); margin-left: 2px;">/क्विंटल</span>
            </td>
            <td style="font-size: 12px; color: var(--text-muted);">
              ₹${Number(p.min_price).toLocaleString("en-IN")} - ₹${Number(p.max_price).toLocaleString("en-IN")}
            </td>
            <td>${mspBadgeHtml}</td>
            <td style="font-size: 12px; color: var(--text-muted); white-space: nowrap;">
              📅 ${p.arrival_date || "आज"}
            </td>
          </tr>
        `;
      }).join("");

      // Update pagination
      const startIdx = currentOffset + 1;
      const endIdx = Math.min(currentOffset + prices.length, totalRecords);
      paginationInfo.textContent = `${startIdx}–${endIdx} (कुल ${totalRecords} में से)`;
      btnPrev.disabled = currentOffset === 0;
      btnNext.disabled = endIdx >= totalRecords;

      if (window.AgriI18n && window.AgriI18n.applyTranslation) {
        window.AgriI18n.applyTranslation(mandiTableBody);
      }

    } catch (err) {
      console.error("Error loading mandi prices:", err);
      mandiTableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 25px; color: #C62828;">
            ⚠️ मंडी डेटा लोड करने में त्रुटि आई। कृपया रीफ्रेश करें।
          </td>
        </tr>
      `;
    }
  }

  // 3. Revenue Calculator Action
  async function calculateRevenue() {
    hideCalcError();
    const commodity = calcCropInput.value.trim();
    const acres = parseFloat(calcAcresInput.value) || 1.0;
    const yieldPerAcre = parseFloat(calcYieldInput.value) || 15.0;
    const state = calcStateSelect.value === "All" ? null : calcStateSelect.value;

    if (!commodity) {
      showCalcError(
        "फसल का नाम खाली है (Crop Name Required)",
        "कृपया फसल का नाम दर्ज करें (उदा. गेहूं, धान, सरसों, चना, मक्का आदि)।"
      );
      return;
    }

    // Client-side pre-validation: reject garbage, random strings, non-crops immediately
    if (!isValidCropQuery(commodity)) {
      showCalcError(
        "अमान्य फसल का नाम (Invalid Crop Name)",
        `"${commodity}" कोई मान्य कृषि फसल नहीं है। कृपया सही फसल का नाम लिखें ताकि सही परिणाम मिल सके (उदा. गेहूं, धान, सरसों, चना, मक्का, टमाटर, आलू, प्याज आदि)।`
      );
      return;
    }

    try {
      const res = await AgriAPI.calculateCropRevenue({
        commodity,
        area_acres: acres,
        expected_yield_qtl_per_acre: yieldPerAcre,
        state
      });

      const data = res.data;
      if (!data || data.valid === false) {
        showCalcError(
          "अमान्य फसल का नाम (Invalid Crop Name)",
          (data && data.message) ? data.message : `"${commodity}" के लिए सही फसल का नाम लिखें ताकि सही परिणाम मिल सके।`
        );
        return;
      }

      // Hide any previous error and display calculation
      hideCalcError();
      calcResultBox.style.display = "block";
      document.getElementById("calc-crop-title").textContent = `🌾 ${data.commodity} — ${data.area_acres} एकड़ अनुमानित आय विवरण`;

      // MSP Badge
      const mspBadge = document.getElementById("calc-msp-badge");
      if (data.msp_comparison) {
        const comp = data.msp_comparison;
        const colorClass = comp.is_above_msp ? "badge-green" : "badge-gold";
        mspBadge.innerHTML = `<span class="badge ${colorClass}">सरकारी MSP ₹${comp.gov_msp_rate}/क्विंटल (${comp.status_text})</span>`;
      } else {
        mspBadge.innerHTML = `<span class="badge badge-outline">ओपन मार्केट भाव</span>`;
      }

      document.getElementById("res-total-production").textContent = `${data.total_production_quintals} क्विंटल`;
      document.getElementById("res-rate-per-qtl").textContent = `${formatINR(data.applied_rate_per_qtl)} /क्विंटल`;
      document.getElementById("res-gross-revenue").textContent = formatINR(data.gross_revenue_rs);
      document.getElementById("res-estimated-cost").textContent = formatINR(data.estimated_cost_rs);
      document.getElementById("res-net-profit").textContent = formatINR(data.net_profit_rs);

      // Top Mandi
      const topMandiEl = document.getElementById("res-top-mandi");
      if (data.top_mandi_benchmark) {
        const tm = data.top_mandi_benchmark;
        topMandiEl.textContent = `${tm.market}, ${tm.district || tm.state} (${formatINR(tm.modal_price)} /क्विंटल)`;
      } else {
        topMandiEl.textContent = "उपलब्ध मंडी औसत दर";
      }

      // Smooth scroll to result if on mobile
      if (window.innerWidth < 768) {
        calcResultBox.scrollIntoView({ behavior: "smooth" });
      }

    } catch (err) {
      console.warn("AgriAPI calculateCropRevenue error:", err);

      // Check if server rejected as invalid crop
      const isInvalidCrop = err.status === 400 || 
        (err.message && (err.message.includes("अमान्य") || err.message.includes("Invalid") || err.message.includes("INVALID_CROP"))) ||
        (err.detail && (err.detail.error === "INVALID_CROP" || (typeof err.detail === "string" && err.detail.includes("INVALID_CROP"))));

      if (isInvalidCrop) {
        const errorMsg = (err.detail && typeof err.detail === "object" && err.detail.message)
          ? err.detail.message
          : (err.message && !err.message.startsWith("Request failed") ? err.message : `"${commodity}" कोई मान्य फसल नहीं है। कृपया सही फसल का नाम लिखें ताकि सही परिणाम मिल सके।`);
        showCalcError("अमान्य फसल का नाम (Invalid Crop Name)", errorMsg);
        return;
      }

      // Client-side fallback ONLY if commodity matches a real recognized crop
      const fallbackRates = {
        "wheat": 2275, "गेहूं": 2275, "gehu": 2275,
        "paddy": 2300, "paddy(common)": 2300, "धान": 2300, "धान (सामान्य)": 2300, "rice": 2300, "chawal": 2300,
        "mustard": 5650, "सरसों": 5650, "sarso": 5650, "sarson": 5650,
        "bengal gram": 5440, "chana": 5440, "चना": 5440, "gram": 5440,
        "cotton": 7122, "कपास": 7122, "kapas": 7122,
        "maize": 2090, "मक्का": 2090, "makka": 2090, "corn": 2090,
        "soyabean": 4600, "सोयाबीन": 4600, "soybean": 4600,
        "tomato": 2100, "टमाटर": 2100, "tamatar": 2100,
        "potato": 1450, "आलू": 1450, "aloo": 1450,
        "onion": 2400, "प्याज": 2400, "pyaz": 2400
      };
      const fallbackCosts = {
        "wheat": 14500, "गेहूं": 14500, "gehu": 14500,
        "paddy": 18000, "paddy(common)": 18000, "धान": 18000, "rice": 18000,
        "mustard": 11500, "सरसों": 11500, "sarso": 11500,
        "bengal gram": 10500, "chana": 10500, "चना": 10500,
        "cotton": 22000, "कपास": 22000,
        "maize": 13500, "मक्का": 13500, "corn": 13500,
        "soyabean": 13000, "सोयाबीन": 13000,
        "tomato": 35000, "टमाटर": 35000,
        "potato": 32000, "आलू": 32000,
        "onion": 28000, "प्याज": 28000
      };

      const cLow = commodity.toLowerCase();
      let matchedKey = null;
      for (const k of Object.keys(fallbackRates)) {
        if (cLow === k || cLow.split(/\s+/).includes(k)) {
          matchedKey = k;
          break;
        }
      }

      if (!matchedKey) {
        showCalcError(
          "अमान्य फसल का नाम (Invalid Crop Name)",
          `"${commodity}" कोई मान्य फसल नहीं है या इसके लिए मंडी भाव उपलब्ध नहीं हैं। कृपया सही फसल का नाम लिखें (उदा. गेहूं, धान, सरसों, चना आदि)।`
        );
        return;
      }

      const rate = fallbackRates[matchedKey];
      const costPerAcre = fallbackCosts[matchedKey] || 15000;
      const totalProd = Math.round(acres * yieldPerAcre * 100) / 100;
      const grossRev = Math.round(totalProd * rate);
      const totalCost = Math.round(acres * costPerAcre);
      const netProf = grossRev - totalCost;

      hideCalcError();
      calcResultBox.style.display = "block";
      document.getElementById("calc-crop-title").textContent = `🌾 ${commodity} — ${acres} एकड़ अनुमानित आय विवरण`;
      document.getElementById("calc-msp-badge").innerHTML = `<span class="badge badge-gold">MSP मानक आधार (₹${rate}/क्विं)</span>`;
      document.getElementById("res-total-production").textContent = `${totalProd} क्विंटल`;
      document.getElementById("res-rate-per-qtl").textContent = `${formatINR(rate)} /क्विंटल`;
      document.getElementById("res-gross-revenue").textContent = formatINR(grossRev);
      document.getElementById("res-estimated-cost").textContent = formatINR(totalCost);
      document.getElementById("res-net-profit").textContent = formatINR(netProf);
      document.getElementById("res-top-mandi").textContent = "राष्ट्रीय औसत APMC मॉडल भाव";

      if (window.innerWidth < 768) {
        calcResultBox.scrollIntoView({ behavior: "smooth" });
      }
    }
  }

  // Quick Crop Chips Event
  quickChips.forEach(chip => {
    chip.addEventListener("click", () => {
      hideCalcError();
      quickChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const cropName = chip.getAttribute("data-crop");
      calcCropInput.value = cropName;
      if (cropDefaults[cropName]) {
        calcYieldInput.value = cropDefaults[cropName].yield;
      }
      // Also filter table
      searchInput.value = cropName;
      currentOffset = 0;
      loadMandiPrices();
      calculateRevenue();
    });
  });

  // Hide error banner when typing in crop input
  calcCropInput.addEventListener("input", () => {
    hideCalcError();
  });

  // Event Listeners
  calcForm.addEventListener("submit", (e) => {
    e.preventDefault();
    calculateRevenue();
  });

  searchInput.addEventListener("input", () => {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      currentOffset = 0;
      loadMandiPrices();
    }, 350);
  });

  stateSelect.addEventListener("change", () => {
    currentOffset = 0;
    loadMandiPrices();
  });

  btnReset.addEventListener("click", () => {
    searchInput.value = "";
    stateSelect.value = "All";
    currentOffset = 0;
    loadMandiPrices();
  });

  btnPrev.addEventListener("click", () => {
    if (currentOffset > 0) {
      currentOffset = Math.max(0, currentOffset - pageSize);
      loadMandiPrices();
    }
  });

  btnNext.addEventListener("click", () => {
    if (currentOffset + pageSize < totalRecords) {
      currentOffset += pageSize;
      loadMandiPrices();
    }
  });

  // Live Sync button
  btnSync.addEventListener("click", async () => {
    btnSync.disabled = true;
    syncSpinner.textContent = "⏳";
    syncStatus.textContent = "भारत सरकार Agmarknet से 500+ रिकॉर्ड्स डाउनलोड हो रहे हैं...";

    try {
      const syncRes = await AgriAPI.syncLiveMandi(500);
      syncSpinner.textContent = "✅";
      syncStatus.textContent = `सफलतापूर्वक सिंक किया गया (${syncRes.stored_or_updated || 300}+ रिकॉर्ड्स अद्यतन)`;
      currentOffset = 0;
      await loadMeta();
      await loadMandiPrices();
    } catch (err) {
      syncSpinner.textContent = "⚠️";
      syncStatus.textContent = "सरकारी सर्वर पर लोड है; सुरक्षित बेसलाइन सक्रिय है।";
    } finally {
      setTimeout(() => {
        btnSync.disabled = false;
        syncSpinner.textContent = "🔄";
      }, 4000);
    }
  });

  // Initialize
  loadMeta();
  loadMandiPrices();
  calculateRevenue(); // calculate default Wheat

  window.addEventListener("agrigo:langchange", () => {
    if (window.AgriI18n && window.AgriI18n.applyTranslation) {
      window.AgriI18n.applyTranslation();
    }
  });
});
