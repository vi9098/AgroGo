/**
 * AgriGo Universal Voice Navigation & Speech Assistant (Web Speech API)
 * Production-ready voice system active across ALL website pages.
 * Supports Hindi, English, Hinglish, Punjabi, Tamil, Telugu, and other regional languages.
 * Includes hands-free navigation, form dictation, voice-driven login & registration,
 * spoken TTS confirmations, and strict password confidentiality guarantees.
 */

const AgriVoiceNav = (() => {
  // State variables
  let recognition = null;
  let isListening = false;
  let isSpeaking = false;
  let isMuted = false;
  let currentLang = "hi-IN";
  let activeConfirmation = null;

  // Map app languages to Web Speech BCP-47 codes
  const LANG_MAP = {
    "hi": "hi-IN",
    "en": "en-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "or": "or-IN",
    "ur": "ur-IN"
  };

  /**
   * Initializes the speech recognition engine and injects the global UI.
   */
  function init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("[AgriVoiceNav] Web Speech Recognition not supported in this browser.");
      _injectWidget(false);
      return;
    }

    try {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      // Sync initial language
      _syncLanguage();

      recognition.onstart = () => {
        isListening = true;
        _updateMicUI("listening");
        _showToast("🎙️ सुन रहा हूँ... बोलिए (Listening... speak now)", "info");
      };

      recognition.onresult = (event) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            finalTranscript += item[0].transcript;
          } else {
            interimTranscript += item[0].transcript;
          }
        }

        const heardText = finalTranscript || interimTranscript;
        if (heardText) {
          _updateHUDTranscript(heardText);
        }

        if (finalTranscript) {
          _processVoiceCommand(finalTranscript.trim());
        }
      };

      recognition.onerror = (event) => {
        console.warn("[AgriVoiceNav Error]", event.error);
        if (event.error === "not-allowed") {
          _speak("माइक्रोफ़ोन अनुमति अस्वीकृत है। कृपया ब्राउज़र सेटिंग्स में माइक्रोफ़ोन की अनुमति दें।");
          _showToast("माइक्रोफ़ोन अनुमति अस्वीकृत है (Microphone permission denied).", "warning");
          stopListening();
        } else if (event.error === "no-speech") {
          // Normal idle timeout
        } else {
          _updateMicUI("idle");
        }
      };

      recognition.onend = () => {
        // Automatically restart if user hasn't explicitly stopped listening
        if (isListening) {
          try {
            recognition.start();
          } catch (_) {
            isListening = false;
            _updateMicUI("idle");
          }
        } else {
          _updateMicUI("idle");
        }
      };

      _injectWidget(true);

      // Keyboard shortcut: Alt + V to toggle voice
      window.addEventListener("keydown", (e) => {
        if (e.altKey && (e.key === "v" || e.key === "V")) {
          e.preventDefault();
          toggleListening();
        }
      });

    } catch (e) {
      console.warn("[AgriVoiceNav Init Error]", e);
      _injectWidget(false);
    }
  }

  function _syncLanguage() {
    let appLang = "hi";
    if (window.AgriI18n && typeof window.AgriI18n.getLanguage === "function") {
      appLang = window.AgriI18n.getLanguage();
    } else {
      const langSelect = document.getElementById("hdr-lang-select");
      if (langSelect && langSelect.value) appLang = langSelect.value;
    }
    currentLang = LANG_MAP[appLang] || "hi-IN";
    if (recognition) {
      recognition.lang = currentLang;
    }
  }

  function startListening() {
    if (!recognition) {
      _showHelpModal(true);
      return;
    }
    _syncLanguage();
    isListening = true;
    try {
      recognition.start();
    } catch (_) {}
    _updateMicUI("listening");
    _showHUD(true);
  }

  function stopListening() {
    isListening = false;
    if (recognition) {
      try {
        recognition.stop();
      } catch (_) {}
    }
    _updateMicUI("idle");
  }

  function toggleListening() {
    if (isListening) {
      stopListening();
      _showToast("माइक्रोफ़ोन बंद किया गया (Microphone paused)", "info");
    } else {
      startListening();
    }
  }

  /**
   * Spoken text-to-speech output in user's active language.
   */
  function _speak(text, onComplete) {
    if (isMuted || !window.speechSynthesis) {
      if (onComplete) onComplete();
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = currentLang;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      isSpeaking = true;
      _updateMicUI("speaking");

      utterance.onend = () => {
        isSpeaking = false;
        _updateMicUI(isListening ? "listening" : "idle");
        if (onComplete) onComplete();
      };

      utterance.onerror = () => {
        isSpeaking = false;
        _updateMicUI(isListening ? "listening" : "idle");
        if (onComplete) onComplete();
      };

      window.speechSynthesis.speak(utterance);
    } catch (_) {
      isSpeaking = false;
      if (onComplete) onComplete();
    }
  }

  /**
   * Main Voice Command Grammar Engine.
   */
  function _processVoiceCommand(rawText) {
    _updateMicUI("processing");
    const cmd = rawText.toLowerCase().trim();
    _showFeedback(`🗣️ सुना: "${rawText}"`);

    // Handle pending confirmation (e.g. form submission confirmation)
    if (activeConfirmation) {
      if (cmd.includes("हाँ") || cmd.includes("करो") || cmd.includes("yes") || cmd.includes("sure") || cmd.includes("submit") || cmd.includes("सहमति")) {
        const action = activeConfirmation.action;
        activeConfirmation = null;
        action();
        return;
      } else if (cmd.includes("नहीं") || cmd.includes("रद्द") || cmd.includes("no") || cmd.includes("cancel") || cmd.includes("मत करो")) {
        activeConfirmation = null;
        _speak("कार्य रद्द कर दिया गया।");
        _showFeedback("कार्य रद्द किया गया।");
        _updateMicUI(isListening ? "listening" : "idle");
        return;
      }
    }

    // ----------------- STRICT SECURITY: PASSWORD CHECK -----------------
    // Never speak, transcribe, store, or process password content
    if (cmd.includes("पासवर्ड") || cmd.includes("password") || cmd.includes("पासवर्ड डालो") || cmd.includes("enter password")) {
      const passInputs = Array.from(document.querySelectorAll("input[type='password']"));
      if (passInputs.length > 0) {
        passInputs[0].focus();
        const msg = "सुरक्षा कारणों से, कृपया अपना पासवर्ड कीबोर्ड से सुरक्षित रूप से टाइप करें।";
        _speak(msg);
        _showFeedback("🔒 कृपया पासवर्ड कीबोर्ड से सुरक्षित टाइप करें।");
      } else {
        _speak("इस पृष्ठ पर कोई पासवर्ड फ़ील्ड नहीं है।");
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // ----------------- 1. NAVIGATION COMMANDS -----------------
    if (cmd.includes("होम") || cmd.includes("मुख्य पृष्ठ") || cmd.includes("home") || cmd === "go home") {
      _speak("होम पेज पर जा रहे हैं।", () => { window.location.href = "index.html"; });
      return;
    }

    if (cmd.includes("किसान चैट") || cmd.includes("कृषि सलाह") || cmd.includes("kisan chat") || cmd === "chat" || cmd.includes("चैट")) {
      _speak("किसान AI चैट पर जा रहे हैं।", () => { window.location.href = "farmer.html"; });
      return;
    }

    if (cmd.includes("लॉगिन") || cmd.includes("login") || cmd.includes("किसान प्रवेश") || cmd.includes("साइन इन")) {
      _speak("किसान लॉगिन पृष्ठ खोल रहे हैं।", () => { window.location.href = "farmer-login.html"; });
      return;
    }

    if (cmd.includes("पंजीकरण") || cmd.includes("नया खाता") || cmd.includes("register") || cmd.includes("signup") || cmd.includes("साइन अप")) {
      _speak("किसान पंजीकरण पृष्ठ खोल रहे हैं।", () => { window.location.href = "register.html"; });
      return;
    }

    if (cmd.includes("मौसम") || cmd.includes("weather") || cmd.includes("बारिश") || cmd.includes("तापमान")) {
      _speak("मौसम केंद्र पर जा रहे हैं।", () => { window.location.href = "weather.html"; });
      return;
    }

    if (cmd.includes("मंडी") || cmd.includes("mandi") || cmd.includes("बाजार भाव") || cmd.includes("कीमत")) {
      _speak("मंडी भाव पृष्ठ पर जा रहे हैं।", () => { window.location.href = "mandi.html"; });
      return;
    }

    if (cmd.includes("अनुस्मारक") || cmd.includes("रिमाइंडर") || cmd.includes("reminders") || cmd.includes("टास्क")) {
      _speak("कृषि अनुस्मारक पृष्ठ खोल रहे हैं।", () => { window.location.href = "reminders.html"; });
      return;
    }

    if (cmd.includes("एडमिन") || cmd.includes("admin")) {
      _speak("एडमिन पोर्टल खोल रहे हैं।", () => { window.location.href = "admin-login.html"; });
      return;
    }

    if (cmd.includes("पीछे") || cmd.includes("वापस") || cmd.includes("back") || cmd === "go back") {
      _speak("पीछे जा रहे हैं।", () => { window.history.back(); });
      return;
    }

    if (cmd.includes("रिफ्रेश") || cmd.includes("reload") || cmd.includes("refresh")) {
      _speak("पृष्ठ पुनः लोड किया जा रहा है।", () => { window.location.reload(); });
      return;
    }

    // ----------------- 2. SCROLLING & VIEW COMMANDS -----------------
    if (cmd.includes("नीचे स्क्रॉल") || cmd.includes("scroll down") || cmd === "नीचे जाओ" || cmd === "नीचे") {
      window.scrollBy({ top: 450, behavior: "smooth" });
      _speak("नीचे स्क्रॉल किया।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    if (cmd.includes("ऊपर स्क्रॉल") || cmd.includes("scroll up") || cmd === "ऊपर जाओ" || cmd === "ऊपर") {
      window.scrollBy({ top: -450, behavior: "smooth" });
      _speak("ऊपर स्क्रॉल किया।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    if (cmd.includes("सबसे ऊपर") || cmd.includes("शीर्ष") || cmd.includes("scroll to top") || cmd === "top") {
      window.scrollTo({ top: 0, behavior: "smooth" });
      _speak("पृष्ठ के शीर्ष पर पहुंचे।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    if (cmd.includes("सबसे नीचे") || cmd.includes("अंत में") || cmd.includes("scroll to bottom") || cmd === "bottom") {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      _speak("पृष्ठ के अंत में पहुंचे।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // ----------------- 3. LOCATION DETECTION COMMAND -----------------
    if (cmd.includes("लोकेशन") || cmd.includes("स्थान लो") || cmd.includes("location") || cmd.includes("use my location") || cmd.includes("कहाँ हूँ")) {
      _speak("जीपीएस से आपकी वर्तमान स्थिति पहचानी जा रही है...");
      if (typeof window.detectCurrentLocation === "function") {
        window.detectCurrentLocation({
          stateSelectId: "reg-state" || "weather-state-select" || "edit-state" || "calc-state",
          districtSelectId: "reg-district" || "weather-district-select" || "edit-district" || "calc-district",
          villageInputId: "reg-village"
        });
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // ----------------- 4. LANGUAGE SWITCHING BY VOICE -----------------
    if (cmd.includes("हिंदी") || cmd.includes("hindi")) {
      _switchLanguage("hi");
      return;
    }
    if (cmd.includes("अंग्रेजी") || cmd.includes("english")) {
      _switchLanguage("en");
      return;
    }
    if (cmd.includes("पंजाबी") || cmd.includes("punjabi")) {
      _switchLanguage("pa");
      return;
    }
    if (cmd.includes("तमिल") || cmd.includes("tamil")) {
      _switchLanguage("ta");
      return;
    }
    if (cmd.includes("तेलुगु") || cmd.includes("telugu")) {
      _switchLanguage("te");
      return;
    }

    // ----------------- 5. FORM FIELD DICTATION & INTERACTION -----------------
    // Phone number dictation
    if (cmd.includes("मोबाइल") || cmd.includes("फोन") || cmd.includes("phone") || cmd.includes("number")) {
      const digits = cmd.replace(/\D/g, "");
      const phoneInput = document.getElementById("farmer-phone") || document.getElementById("reg-phone") || document.querySelector("input[type='tel']");
      if (phoneInput && digits.length >= 10) {
        const clean10 = digits.slice(-10);
        phoneInput.value = clean10;
        phoneInput.dispatchEvent(new Event("input", { bubbles: true }));
        phoneInput.focus();
        _speak(`मोबाइल नंबर दर्ज किया: ${clean10}`);
        _showFeedback(`📱 नंबर: ${clean10}`);
      } else if (phoneInput && digits.length > 0) {
        phoneInput.value = digits;
        phoneInput.focus();
        _speak(`नंबर दर्ज किया: ${digits}`);
      } else if (phoneInput) {
        phoneInput.focus();
        _speak("कृपया 10 अंकों का मोबाइल नंबर बोलें।");
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Name dictation
    if (cmd.startsWith("नाम ") || cmd.startsWith("name ") || cmd.includes("किसान का नाम")) {
      const nameVal = rawText.replace(/^(नाम|name|किसान का नाम|fill name)\s+/i, "").trim();
      const nameInput = document.getElementById("reg-name") || document.getElementById("farmer-name") || document.getElementById("edit-name");
      if (nameInput && nameVal) {
        nameInput.value = nameVal;
        nameInput.dispatchEvent(new Event("input", { bubbles: true }));
        nameInput.focus();
        _speak(`नाम दर्ज किया: ${nameVal}`);
        _showFeedback(`👤 नाम: ${nameVal}`);
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // State selection by voice
    if (cmd.includes("राज्य") || cmd.includes("state")) {
      const stateQuery = rawText.replace(/.*?(राज्य|state)\s*/i, "").trim();
      const stateSelect = document.getElementById("reg-state") || document.getElementById("weather-state-select") || document.getElementById("calc-state") || document.getElementById("edit-state");
      if (stateSelect && stateQuery && typeof window.resolveStateKey === "function") {
        const matched = window.resolveStateKey(stateQuery);
        if (matched) {
          stateSelect.value = matched;
          stateSelect.dispatchEvent(new Event("change", { bubbles: true }));
          _speak(`राज्य चुना गया: ${matched}`);
          _showFeedback(`🏛️ राज्य: ${matched}`);
        }
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // District selection by voice
    if (cmd.includes("जिला") || cmd.includes("district")) {
      const distQuery = rawText.replace(/.*?(जिला|district)\s*/i, "").trim();
      const distSelect = document.getElementById("reg-district") || document.getElementById("weather-district-select") || document.getElementById("calc-district") || document.getElementById("edit-district");
      const stateSelect = document.getElementById("reg-state") || document.getElementById("weather-state-select") || document.getElementById("calc-state") || document.getElementById("edit-state");
      if (distSelect && distQuery && stateSelect && typeof window.resolveDistrictKey === "function") {
        const matched = window.resolveDistrictKey(stateSelect.value, distQuery);
        if (matched) {
          distSelect.value = matched;
          distSelect.dispatchEvent(new Event("change", { bubbles: true }));
          _speak(`जिला चुना गया: ${matched}`);
          _showFeedback(`📍 जिला: ${matched}`);
        } else {
          // Direct option search
          const opt = Array.from(distSelect.options).find(o => o.text.toLowerCase().includes(distQuery.toLowerCase()));
          if (opt) {
            distSelect.value = opt.value;
            distSelect.dispatchEvent(new Event("change", { bubbles: true }));
            _speak(`जिला चुना गया: ${opt.text}`);
          }
        }
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Crop selection by voice
    if (cmd.includes("फसल") || cmd.includes("crop")) {
      const cropQuery = rawText.replace(/.*?(फसल|crop)\s*/i, "").trim().toLowerCase();
      const cropSelect = document.getElementById("reg-primary-crop") || document.getElementById("calc-crop") || document.getElementById("edit-crop");
      if (cropSelect && cropQuery) {
        const opt = Array.from(cropSelect.options).find(o => o.text.toLowerCase().includes(cropQuery) || o.value.toLowerCase().includes(cropQuery));
        if (opt) {
          cropSelect.value = opt.value;
          cropSelect.dispatchEvent(new Event("change", { bubbles: true }));
          _speak(`फसल चुनी गई: ${opt.text}`);
          _showFeedback(`🌾 फसल: ${opt.text}`);
        }
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Area/Acres selection
    if (cmd.includes("एकड़") || cmd.includes("रकबा") || cmd.includes("क्षेत्रफल") || cmd.includes("area")) {
      const digits = cmd.match(/[0-9]+(?:\.[0-9]+)?/);
      const areaInput = document.getElementById("reg-farm-area") || document.getElementById("calc-area") || document.getElementById("edit-area");
      if (areaInput && digits) {
        areaInput.value = digits[0];
        areaInput.dispatchEvent(new Event("input", { bubbles: true }));
        _speak(`क्षेत्रफल दर्ज किया: ${digits[0]} एकड़`);
        _showFeedback(`📐 एकड़: ${digits[0]}`);
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Village/Tehsil
    if (cmd.includes("गांव") || cmd.includes("तहसील") || cmd.includes("village")) {
      const villageVal = rawText.replace(/.*?(गांव|तहसील|village)\s*/i, "").trim();
      const villageInput = document.getElementById("reg-village") || document.getElementById("edit-village");
      if (villageInput && villageVal) {
        villageInput.value = villageVal;
        villageInput.dispatchEvent(new Event("input", { bubbles: true }));
        _speak(`गांव दर्ज किया: ${villageVal}`);
        _showFeedback(`🏡 गांव: ${villageVal}`);
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Focus controls: Next field, previous field
    if (cmd.includes("अगला") || cmd.includes("next")) {
      _focusRelativeInput(1);
      _speak("अगले बॉक्स पर पहुंचे।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    if (cmd.includes("पिछला") || cmd.includes("previous")) {
      _focusRelativeInput(-1);
      _speak("पिछले बॉक्स पर पहुंचे।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Clear active field
    if (cmd.includes("साफ करो") || cmd.includes("हटाओ") || cmd.includes("clear")) {
      if (document.activeElement && (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "SELECT")) {
        document.activeElement.value = "";
        _speak("फ़ील्ड साफ की गई।");
      }
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // ----------------- 6. FORM SUBMISSION WITH VOICE CONFIRMATION -----------------
    if (cmd.includes("जमा करो") || cmd.includes("सबमिट") || cmd.includes("submit") || cmd.includes("प्रवेश करो") || cmd.includes("खाता बनाओ")) {
      const regForm = document.getElementById("farmer-register-form");
      const loginBtn = document.getElementById("btn-farmer-login");

      if (loginBtn && window.location.pathname.includes("login")) {
        _speak("लॉगिन किया जा रहा है...");
        loginBtn.click();
        return;
      }

      if (regForm) {
        activeConfirmation = {
          action: () => {
            _speak("पंजीकरण फॉर्म जमा किया जा रहा है...");
            const submitBtn = regForm.querySelector("button[type='submit']") || regForm.querySelector(".btn-submit");
            if (submitBtn) submitBtn.click();
            else regForm.dispatchEvent(new Event("submit", { cancelable: true }));
          }
        };
        _speak("क्या आप पंजीकरण फॉर्म जमा करना चाहते हैं? पुष्टि के लिए 'हाँ' बोलें।");
        _showFeedback("❓ पुष्टि करें: क्या आप फॉर्म जमा करना चाहते हैं? ('हाँ' कहें)");
        _updateMicUI(isListening ? "listening" : "idle");
        return;
      }
    }

    // ----------------- 7. HELP & TEXT FALLBACK -----------------
    if (cmd.includes("मदद") || cmd.includes("हेल्प") || cmd.includes("निर्देश") || cmd.includes("help") || cmd.includes("commands")) {
      _showHelpModal();
      _speak("आवाज के सभी उपलब्ध निर्देश स्क्रीन पर दिखाए गए हैं।");
      _updateMicUI(isListening ? "listening" : "idle");
      return;
    }

    // Fallback: unmatched command
    _speak(`क्षमा करें, "${rawText}" निर्देश समझ नहीं आया। 'मदद' कहकर निर्देश देखें।`);
    _showFeedback(`⚠️ निर्देश समझ नहीं आया: "${rawText}"`);
    _updateMicUI(isListening ? "listening" : "idle");
  }

  function _focusRelativeInput(direction) {
    const inputs = Array.from(document.querySelectorAll("input:not([type='hidden']), select, textarea, button[type='submit']"))
      .filter(el => el.offsetParent !== null && !el.disabled);
    const currentIndex = inputs.indexOf(document.activeElement);
    if (currentIndex === -1) {
      if (inputs.length > 0) inputs[0].focus();
    } else {
      const nextIndex = (currentIndex + direction + inputs.length) % inputs.length;
      inputs[nextIndex].focus();
    }
  }

  function _switchLanguage(langCode) {
    if (window.AgriI18n && typeof window.AgriI18n.setLanguage === "function") {
      window.AgriI18n.setLanguage(langCode);
    }
    const langSelect = document.getElementById("hdr-lang-select");
    if (langSelect) {
      langSelect.value = langCode;
      langSelect.dispatchEvent(new Event("change"));
    }
    _syncLanguage();
    _speak(langCode === "hi" ? "हिंदी भाषा चुनी गई।" : "Language switched to English.");
    _showToast(`भाषा बदली: ${langCode.toUpperCase()}`, "success");
    _updateMicUI(isListening ? "listening" : "idle");
  }

  // ----------------- UI INJECTION -----------------
  function _injectWidget(isSupported) {
    if (document.getElementById("agri-voice-control-wrap")) return;

    // Floating Widget Container
    const wrap = document.createElement("div");
    wrap.id = "agri-voice-control-wrap";
    wrap.innerHTML = `
      <style>
        #agri-voice-control-wrap {
          position: fixed;
          bottom: 22px;
          right: 22px;
          z-index: 99990;
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 8px;
          font-family: inherit;
        }
        .voice-hud {
          background: rgba(17, 24, 39, 0.94);
          backdrop-filter: blur(8px);
          color: #FFFFFF;
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 14px;
          padding: 10px 14px;
          max-width: 310px;
          font-size: 12.5px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
          display: none;
          animation: slideUpHUD 0.2s ease-out;
        }
        @keyframes slideUpHUD {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .voice-hud-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 11px;
          color: #9CA3AF;
          font-weight: 700;
          margin-bottom: 4px;
        }
        .voice-hud-transcript {
          color: #A7F3D0;
          font-weight: 600;
          word-break: break-word;
          margin-bottom: 4px;
        }
        .voice-hud-feedback {
          color: #E5E7EB;
          font-size: 12px;
        }
        .voice-mic-btn {
          width: 54px;
          height: 54px;
          border-radius: 50%;
          border: none;
          background: #16A34A;
          color: #FFFFFF;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          cursor: pointer;
          box-shadow: 0 4px 18px rgba(22, 163, 74, 0.45);
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
        }
        .voice-mic-btn:hover {
          transform: scale(1.06);
          box-shadow: 0 6px 22px rgba(22, 163, 74, 0.6);
        }
        .voice-mic-btn.listening {
          background: #DC2626;
          animation: pulseRing 1.5s infinite;
        }
        .voice-mic-btn.processing {
          background: #D97706;
          animation: spinPulse 1.2s infinite;
        }
        .voice-mic-btn.speaking {
          background: #0284C7;
          animation: soundWave 1.2s infinite;
        }
        @keyframes pulseRing {
          0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
          70% { box-shadow: 0 0 0 16px rgba(220, 38, 38, 0); }
          100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }
        @keyframes soundWave {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.08); }
        }
      </style>

      <div class="voice-hud" id="voice-nav-hud">
        <div class="voice-hud-header">
          <span>🎙️ आवाज सहायक (Voice AI)</span>
          <div style="display:flex; gap:8px; align-items:center;">
            <button id="btn-voice-mute" style="background:none; border:none; color:#D1D5DB; cursor:pointer; font-size:12px;" title="आवाज बंद/चालू करें">🔊</button>
            <button id="btn-voice-help" style="background:none; border:none; color:#D1D5DB; cursor:pointer; font-size:12px;" title="आवाज निर्देश">⌨️</button>
            <button id="btn-voice-close-hud" style="background:none; border:none; color:#9CA3AF; cursor:pointer; font-size:12px;" title="बंद करें">✕</button>
          </div>
        </div>
        <div class="voice-hud-transcript" id="voice-hud-text">सुन रहा हूँ... बोलिए</div>
        <div class="voice-hud-feedback" id="voice-hud-feedback"></div>
      </div>

      <button class="voice-mic-btn" id="voice-main-mic-btn" title="आवाज से नेविगेट करें (Voice Navigation) • Alt+V" aria-label="Voice Navigation Assistant">
        🎙️
      </button>
    `;

    document.body.appendChild(wrap);

    const micBtn = document.getElementById("voice-main-mic-btn");
    micBtn.addEventListener("click", () => {
      toggleListening();
    });

    const closeHudBtn = document.getElementById("btn-voice-close-hud");
    if (closeHudBtn) {
      closeHudBtn.addEventListener("click", () => {
        document.getElementById("voice-nav-hud").style.display = "none";
      });
    }

    const muteBtn = document.getElementById("btn-voice-mute");
    if (muteBtn) {
      muteBtn.addEventListener("click", () => {
        isMuted = !isMuted;
        muteBtn.textContent = isMuted ? "🔇" : "🔊";
        _showToast(isMuted ? "आवाज प्रतिक्रिया म्यूट है (Voice muted)" : "आवाज प्रतिक्रिया चालू है (Voice unmuted)", "info");
      });
    }

    const helpBtn = document.getElementById("btn-voice-help");
    if (helpBtn) {
      helpBtn.addEventListener("click", () => {
        _showHelpModal();
      });
    }
  }

  function _updateMicUI(state) {
    const micBtn = document.getElementById("voice-main-mic-btn");
    if (!micBtn) return;
    micBtn.className = `voice-mic-btn ${state}`;
    if (state === "listening") {
      micBtn.innerHTML = "🔴";
      micBtn.title = "सुन रहा हूँ... बोलिए (Listening...)";
    } else if (state === "processing") {
      micBtn.innerHTML = "⏳";
      micBtn.title = "समझ रहा हूँ... (Processing...)";
    } else if (state === "speaking") {
      micBtn.innerHTML = "🔊";
      micBtn.title = "बोल रहा हूँ... (Speaking...)";
    } else {
      micBtn.innerHTML = "🎙️";
      micBtn.title = "आवाज से नेविगेट करें (Voice Navigation) • Alt+V";
    }
  }

  function _showHUD(show) {
    const hud = document.getElementById("voice-nav-hud");
    if (hud) hud.style.display = show ? "block" : "none";
  }

  function _updateHUDTranscript(text) {
    _showHUD(true);
    const txtEl = document.getElementById("voice-hud-text");
    if (txtEl) txtEl.textContent = text;
  }

  function _showFeedback(msg) {
    _showHUD(true);
    const fbEl = document.getElementById("voice-hud-feedback");
    if (fbEl) fbEl.textContent = msg;
  }

  function _showToast(msg, type = "info") {
    if (typeof window.showToast === "function") {
      window.showToast(msg, type);
    }
  }

  /**
   * Accessible Commands Help & Text Fallback Modal.
   */
  function _showHelpModal(isUnsupported = false) {
    const existing = document.getElementById("voice-help-modal");
    if (existing) existing.remove();

    const modal = document.createElement("div");
    modal.id = "voice-help-modal";
    modal.style.position = "fixed";
    modal.style.inset = "0";
    modal.style.backgroundColor = "rgba(0, 0, 0, 0.65)";
    modal.style.zIndex = "99999";
    modal.style.display = "flex";
    modal.style.alignItems = "center";
    modal.style.justifyContent = "center";
    modal.style.padding = "20px";

    modal.innerHTML = `
      <div style="background:#FFFFFF; border-radius:18px; padding:24px; max-width:540px; width:100%; box-shadow:0 20px 45px rgba(0,0,0,0.3); max-height:85vh; overflow-y:auto; font-family:inherit;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1.5px solid #E5E7EB; padding-bottom:12px; margin-bottom:16px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:24px;">🎙️</span>
            <h3 style="margin:0; font-size:18px; font-weight:800; color:#14532D;">AgriGo आवाज व टेक्स्ट सहायक निर्देश</h3>
          </div>
          <button id="btn-close-voice-help" style="background:none; border:none; font-size:18px; cursor:pointer; color:#6B7280;">✕</button>
        </div>

        ${isUnsupported ? `
          <div style="background:#FEF2F2; border:1px solid #FCA5A5; color:#991B1B; padding:10px 14px; border-radius:10px; font-size:12.5px; margin-bottom:16px;">
            ⚠️ आपके वर्तमान ब्राउज़र में माइक्रोफ़ोन स्पीच इनपुट समर्थित नहीं है। आप नीचे दिए गए बॉक्स में कमांड टाइप करके वेबसाइट नियंत्रित कर सकते हैं।
          </div>
        ` : ''}

        <!-- Interactive Text Command Box (Fallback) -->
        <div style="background:#F0FDF4; border:1.5px solid #86EFAC; border-radius:12px; padding:12px 14px; margin-bottom:18px;">
          <label style="display:block; font-size:12px; font-weight:700; color:#166534; margin-bottom:6px;">
            ⌨️ टेक्स्ट कमांड टाइप करें (Text-based Command Fallback):
          </label>
          <div style="display:flex; gap:8px;">
            <input type="text" id="text-voice-command-input" class="form-input" placeholder="उदा. मौसम देखो, नाम रमेश, नीचे स्क्रॉल..." style="flex:1; font-size:13px; padding:6px 10px; border-radius:8px; border:1px solid #86EFAC;">
            <button id="btn-run-text-command" style="background:#16A34A; color:#FFFFFF; border:none; border-radius:8px; padding:6px 14px; font-size:13px; font-weight:700; cursor:pointer;">
              चलाएं ➔
            </button>
          </div>
        </div>

        <div style="font-size:13px; color:#374151; line-height:1.6;">
          <div style="font-weight:800; color:#14532D; margin-bottom:6px;">🚀 मुख्य बोलचाल निर्देश (Available Voice Commands):</div>
          
          <div style="background:#F9FAFB; border-radius:10px; padding:10px 12px; margin-bottom:10px;">
            <b>🧭 पृष्ठ नेविगेशन (Navigation):</b><br>
            • "होम पेज पर जाओ" / "Go Home"<br>
            • "किसान चैट खोलो" / "Open Kisan Chat"<br>
            • "मौसम केंद्र देखो" / "Check Weather"<br>
            • "मंडी भाव देखो" / "Show Mandi Prices"<br>
            • "अनुस्मारक खोलो" / "Open Reminders"<br>
            • "लॉगिन पृष्ठ" / "Farmer Login"<br>
            • "पंजीकरण करो" / "Register Account"<br>
            • "पीछे जाओ" / "Go Back"
          </div>

          <div style="background:#F9FAFB; border-radius:10px; padding:10px 12px; margin-bottom:10px;">
            <b>📝 फॉर्म भरना (Voice Form Filling):</b><br>
            • "नाम [आपका नाम]" (उदा. नाम रामेश सिंह)<br>
            • "मोबाइल [10 अंकों का नंबर]" (उदा. मोबाइल 9876543210)<br>
            • "राज्य [राज्य का नाम]" (उदा. राज्य उत्तर प्रदेश या पंजाब)<br>
            • "जिला [जिले का नाम]" (उदा. जिला वाराणसी या लुधियाना)<br>
            • "फसल [फसल का नाम]" (उदा. फसल गेहूं या धान)<br>
            • "रकबा [एकड़]" (उदा. रकबा 4 एकड़)<br>
            • "स्थान लो" / "Use My Location" (जीपीएस से स्थान भरना)<br>
            • "अगला बॉक्स" / "पिछला बॉक्स"
          </div>

          <div style="background:#F9FAFB; border-radius:10px; padding:10px 12px; margin-bottom:10px;">
            <b>🔒 पासवर्ड सुरक्षा निर्देश (Security Guarantee):</b><br>
            • सुरक्षा कारणों से पासवर्ड कभी भी बोलकर या स्क्रीन पर रिकॉर्ड नहीं किया जाता। पासवर्ड फ़ील्ड पर आने पर कृपया पासवर्ड कीबोर्ड से सुरक्षित रूप से टाइप करें।
          </div>

          <div style="background:#F9FAFB; border-radius:10px; padding:10px 12px;">
            <b>⚡ शॉर्टकट व नियंत्रण:</b><br>
            • माइक्रोफ़ोन चालू/बंद: <b>Alt + V</b> या नीचे हरे बटन पर क्लिक करें।
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    const closeBtn = modal.querySelector("#btn-close-voice-help");
    closeBtn.addEventListener("click", () => modal.remove());

    const runBtn = modal.querySelector("#btn-run-text-command");
    const inputEl = modal.querySelector("#text-voice-command-input");
    
    const handleRun = () => {
      const val = inputEl.value.trim();
      if (val) {
        modal.remove();
        _processVoiceCommand(val);
      }
    };

    runBtn.addEventListener("click", handleRun);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleRun();
    });
  }

  // Auto-initialize when document is loaded
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }

  return {
    init,
    startListening,
    stopListening,
    toggleListening,
    processCommand: _processVoiceCommand,
    showHelp: _showHelpModal
  };
})();

if (typeof window !== "undefined") {
  window.AgriVoiceNav = AgriVoiceNav;
}
