/**
 * AgriGo Universal Site Header & Taskbar
 * Injects the shared 2-layer header into every page
 * Integrated with server-side session user status and live weather/mandi data.
 */

(function () {
  function injectHeader(opts) {
    opts = opts || {};
    const page = opts.page || 'home';

    // Page label map
    const pages = [
      { key: 'home',      url: 'index.html',     icon: '🏠', label: 'होम (Home)' },
      { key: 'farmer',    url: 'farmer.html',    icon: '🌾', label: 'किसान AI चैट' },
      { key: 'register',  url: 'register.html',  icon: '🌱', label: 'पंजीकरण (Register)' },
      { key: 'reminders', url: 'reminders.html', icon: '⏰', label: 'अनुस्मारक' },
      { key: 'weather',   url: 'weather.html',   icon: '🌤️', label: 'मौसम केंद्र' },
      { key: 'mandi',     url: 'mandi.html',     icon: '💰', label: 'मंडी भाव', gold: true },
      { key: 'admin',     url: 'admin-login.html', icon: '🛡️', label: 'एडमिन' },
    ];

    const headerHTML = `
      <header class="site-header" id="site-header">
        <div class="header-top">
          <!-- Brand -->
          <a href="index.html" class="brand-logo">
            <div class="brand-icon">🌾</div>
            <div>
              <span>AgriGo</span>
              <span class="brand-tagline">भारत का कृषि AI मंच • AI 2026</span>
            </div>
          </a>

          <!-- Status Pills (Center) -->
          <div class="header-status" id="header-status">
            <a href="weather.html" class="status-pill live" id="hdr-weather-pill" title="मौसम केंद्र खोलें">
              🌤️ <span id="hdr-temp">मौसम लोड हो रहा है...</span>
            </a>
            <span class="status-pill" id="hdr-mandi-pill" title="आज के ताजा मंडी भाव">
              💰 <span id="hdr-mandi-text">मंडी भाव लोड हो रहे हैं...</span>
            </span>
          </div>

          <!-- Actions & User Profile -->
          <div class="header-actions">
            <!-- Real-data Notification Bell -->
            <div class="notif-bell-wrap" id="hdr-notif-wrap" style="display:none;">
              <button class="notif-bell-btn" id="hdr-notif-btn" onclick="window.AgriHeader.toggleNotifications()" title="सूचनाएं व कृषि अनुस्मारक">
                🔔
                <span class="notif-badge" id="hdr-notif-badge" style="display:none;">0</span>
              </button>
              <div class="notif-dropdown" id="hdr-notif-dropdown" style="display:none;">
                <div class="notif-header">
                  <h4>🔔 कृषि कार्य सूचनाएं</h4>
                  <span id="notif-count-text" style="font-size:11px; font-weight:700; color:#059669;">0 कार्य लंबित</span>
                </div>
                <div class="notif-list" id="hdr-notif-list">
                  <div style="padding:20px; text-align:center; color:#6B7280; font-size:12px;">कोई लंबित अनुस्मारक नहीं है।</div>
                </div>
                <div class="notif-footer">
                  <button id="btn-request-browser-notif" onclick="window.AgriHeader.requestBrowserNotifications()" style="background:none; border:none; color:#0284C7; font-size:11px; cursor:pointer; font-weight:700; padding:0;">
                    📲 ब्राउज़र अलर्ट सक्षम करें
                  </button>
                  <a href="reminders.html" style="color:#059669; font-size:11.5px; font-weight:700; text-decoration:none;">सभी देखें ➔</a>
                </div>
              </div>
            </div>

            <div id="hdr-user-badge" style="display:none; align-items:center; gap:8px;">
              <span id="hdr-user-name" style="font-size:12px; font-weight:700; color:#FFF; background:rgba(255,255,255,0.12); padding:4px 10px; border-radius:999px;">
                👤
              </span>
              <button onclick="window.AgriHeader.handleLogout()" style="background:none; border:1px solid rgba(255,255,255,0.25); color:rgba(255,255,255,0.85); font-size:11px; padding:3px 8px; border-radius:999px; cursor:pointer;" title="लॉगआउट करें">
                लॉगआउट
              </button>
            </div>

            <div id="hdr-login-actions" style="display:inline-flex; align-items:center; gap:6px;">
              <a href="farmer-login.html" id="hdr-kisan-login-btn" style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.3); color:#FFFFFF; font-size:11.5px; font-weight:700; padding:4px 12px; border-radius:999px; text-decoration:none; white-space:nowrap; transition:all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.18)'">
                🌾 किसान लॉगिन
              </a>
            </div>

            <select id="hdr-lang-select" class="form-select" style="width: auto; padding: 4px 8px; font-size: 11.5px; background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.2); color: #FFF; border-radius: var(--r-full);" title="भाषा चुनें">
              <option value="hi" style="color:#000;">🇮🇳 हिंदी</option>
              <option value="en" style="color:#000;">🇬🇧 English</option>
              <option value="ta" style="color:#000;">🌺 தமிழ்</option>
              <option value="te" style="color:#000;">🌻 తెలుగు</option>
              <option value="pa" style="color:#000;">🌾 ਪੰਜਾਬੀ</option>
            </select>
          </div>
        </div>

        <!-- Taskbar -->
        <nav class="taskbar" role="navigation" aria-label="Main Navigation">
          ${pages.map(p => `
            <a href="${p.url}" class="task-link${p.key === page ? ' active' : ''}${p.gold ? ' gold' : ''}" title="${p.label}">
              <span>${p.icon}</span> ${p.label}
            </a>
          `).join('<div class="task-divider"></div>')}
          <div class="task-divider" style="margin-left: auto;"></div>
          <span class="task-link" style="opacity:0.6; font-size:11.5px; cursor:default;">
            📡 data.gov.in Agmarknet
          </span>
        </nav>
      </header>
    `;

    // Find or create insertion point
    const target = document.getElementById('site-header-mount') || document.body;
    if (document.getElementById('site-header-mount')) {
      target.innerHTML = headerHTML;
    } else {
      document.body.insertAdjacentHTML('afterbegin', headerHTML);
    }

    // Connect language selector to site-wide bilingual engine
    const langSel = document.getElementById('hdr-lang-select');
    if (langSel) {
      if (window.AgriI18n) {
        langSel.value = window.AgriI18n.getLanguage();
      }
      langSel.addEventListener('change', (e) => {
        if (window.AgriI18n) {
          window.AgriI18n.setLanguage(e.target.value);
        }
      });
    }

    if (window.AgriI18n && window.AgriI18n.applyTranslation) {
      window.AgriI18n.applyTranslation();
    }

    _checkUserSession(page);
    if (page !== 'admin') {
      _loadHeaderWeather();
      _loadHeaderMandi();
    }
  }

  async function _checkUserSession(page) {
    try {
      if (window.AgriAPI && window.AgriAPI.getMe) {
        const me = await window.AgriAPI.getMe();
        if (me && me.authenticated && me.user) {

          const notifWrap = document.getElementById("hdr-notif-wrap");
          if (notifWrap) {
            notifWrap.style.display = "inline-flex";
            _loadUserNotifications(me.user.id);
          }

          const badge = document.getElementById("hdr-user-badge");
          const nameSpan = document.getElementById("hdr-user-name");
          if (badge && nameSpan) {
            badge.style.display = "inline-flex";
            const roleTag = me.user.role === "admin" ? "🛡️ " : "🌾 ";
            nameSpan.innerText = `${roleTag}${me.user.name || me.user.id}`;

            if (me.user.role === "admin") {
              const adminLinks = document.querySelectorAll('a[href="admin-login.html"]');
              adminLinks.forEach(lnk => lnk.setAttribute("href", "admin.html"));
            }

            const loginActions = document.getElementById("hdr-login-actions");
            if (loginActions) {
              loginActions.style.display = "none";
            }
          }
        }
      }
    } catch (_) {}
  }

  async function _loadUserNotifications(userId) {
    if (!userId) return;
    try {
      const res = await window.AgriAPI.getFarmerReminders(userId);
      if (!res || !res.reminders) return;

      const incomplete = res.reminders.filter(r => !r.is_completed);

      const badge = document.getElementById("hdr-notif-badge");
      const countText = document.getElementById("notif-count-text");
      const listContainer = document.getElementById("hdr-notif-list");

      if (badge) {
        badge.innerText = incomplete.length;
        badge.style.display = incomplete.length > 0 ? "inline-block" : "none";
      }

      if (countText) {
        countText.innerText = `${incomplete.length} कार्य लंबित`;
      }

      if (!listContainer) return;

      if (incomplete.length === 0) {
        listContainer.innerHTML = `
          <div style="padding: 24px; text-align: center; color: #6B7280; font-size: 12.5px;">
            <span style="font-size: 28px; display: block; margin-bottom: 6px;">🎉</span>
            सभी कृषि कार्य पूर्ण हैं! कोई नया रिमाइंडर लंबित नहीं है।
          </div>
        `;
        return;
      }

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      listContainer.innerHTML = "";
      incomplete.forEach(r => {
        let catIcon = "📋";
        const t = (r.reminder_type || "").toLowerCase();
        if (t.includes("irrigation") || t.includes("पानी") || t.includes("सिंचाई")) catIcon = "💧";
        else if (t.includes("fertilizer") || t.includes("खाद") || t.includes("उर्वरक")) catIcon = "🌱";
        else if (t.includes("pest") || t.includes("कीट") || t.includes("रोग")) catIcon = "🛡️";
        else if (t.includes("weeding") || t.includes("निराई")) catIcon = "🌿";
        else if (t.includes("harvest") || t.includes("कटाई")) catIcon = "🌾";

        let urgencyClass = "upcoming";
        let urgencyText = r.due_date || "शीघ्र";

        const match = (r.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
        if (match) {
          const due = new Date(match[0]);
          due.setHours(0, 0, 0, 0);
          const diffDays = Math.round((due - today) / (1000 * 60 * 60 * 24));
          if (diffDays < 0) {
            urgencyClass = "overdue";
            urgencyText = `⚠️ अतिदेय (${Math.abs(diffDays)} दिन पूर्व)`;
          } else if (diffDays === 0) {
            urgencyClass = "today";
            urgencyText = `🔥 आज ही देय`;
          } else {
            urgencyClass = "upcoming";
            urgencyText = `⏳ ${diffDays} दिन शेष (${r.due_date})`;
          }
        }

        const item = document.createElement("div");
        item.className = `notif-item ${urgencyClass}`;
        item.innerHTML = `
          <div class="notif-item-icon">${catIcon}</div>
          <div class="notif-item-content">
            <div class="notif-item-title">${r.title}</div>
            <div class="notif-item-meta">${urgencyText}</div>
            <button class="notif-item-btn" onclick="window.AgriHeader.completeReminderFromNotif('${r.id}')">
              ✓ पूर्ण करें
            </button>
          </div>
        `;
        listContainer.appendChild(item);
      });

      // Browser Notification trigger for urgent tasks if permission granted
      if ("Notification" in window && Notification.permission === "granted" && !sessionStorage.getItem("notif_alert_shown")) {
        const urgent = incomplete.filter(r => {
          const m = (r.due_date || "").match(/\d{4}-\d{2}-\d{2}/);
          if (!m) return false;
          const d = new Date(m[0]);
          d.setHours(0, 0, 0, 0);
          return d <= today;
        });

        if (urgent.length > 0) {
          sessionStorage.setItem("notif_alert_shown", "true");
          new Notification("AgriGo कृषि अनुस्मारक", {
            body: `आपके ${urgent.length} कृषि कार्य (उदा: ${urgent[0].title}) लंबित हैं!`,
            icon: "favicon.ico"
          });
        }
      }
    } catch (e) {
      console.warn("Could not load notifications:", e);
    }
  }

  function toggleNotifications() {
    const dropdown = document.getElementById("hdr-notif-dropdown");
    if (!dropdown) return;
    dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
  }

  async function completeReminderFromNotif(reminderId) {
    try {
      await window.AgriAPI.toggleReminder(reminderId);
      const me = await window.AgriAPI.getMe();
      if (me && me.user) {
        await _loadUserNotifications(me.user.id);
      }
      if (typeof loadReminders === "function") {
        await loadReminders();
      }
      if (typeof loadFarmerReminders === "function") {
        await loadFarmerReminders();
      }
    } catch (err) {
      alert("स्थिति बदलने में त्रुटि: " + err.message);
    }
  }

  async function requestBrowserNotifications() {
    if (!("Notification" in window)) {
      alert("आपके ब्राउज़र में नोटिफिकेशन समर्थित नहीं है।");
      return;
    }
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      alert("✓ ब्राउज़र नोटिफिकेशन सक्षम किए गए हैं।");
      const me = await window.AgriAPI.getMe();
      if (me && me.user) {
        await _loadUserNotifications(me.user.id);
      }
    } else {
      alert("ब्राउज़र नोटिफिकेशन अनुमति अस्वीकृत की गई।");
    }
  }

  // Close notification dropdown when clicking outside
  document.addEventListener('click', (e) => {
    const wrap = document.getElementById("hdr-notif-wrap");
    const dropdown = document.getElementById("hdr-notif-dropdown");
    if (wrap && dropdown && !wrap.contains(e.target)) {
      dropdown.style.display = "none";
    }
  });

  async function _loadHeaderWeather() {
    try {
      const BASE = (window.location.protocol === 'file:') ? 'http://127.0.0.1:8000/api/v1' : '/api/v1';
      const c = new AbortController();
      const t = setTimeout(() => c.abort(), 3500);
      const res = await fetch(`${BASE}/agriculture/weather`, { credentials: "include", signal: c.signal });
      clearTimeout(t);
      const data = await res.json();
      const el = document.getElementById('hdr-temp');
      if (el && data.temperature_c !== undefined) {
        const rain = data.rain_prob_today_pct !== undefined ? `| 🌧️ ${data.rain_prob_today_pct}%` : '';
        const loc = data.location ? data.location.split("(")[0].trim() : "मौसम";
        el.textContent = `${loc}: ${data.temperature_c}°C ${rain}`;
      }
    } catch (_) {
      const el = document.getElementById('hdr-temp');
      if (el) el.textContent = 'Open-Meteo मौसम';
    }
  }

  async function _loadHeaderMandi() {
    try {
      const BASE = (window.location.protocol === 'file:') ? 'http://127.0.0.1:8000/api/v1' : '/api/v1';
      const c = new AbortController();
      const t = setTimeout(() => c.abort(), 3500);
      const res = await fetch(`${BASE}/agriculture/market/live?limit=3`, { credentials: "include", signal: c.signal });
      clearTimeout(t);
      const data = await res.json();
      const el = document.getElementById('hdr-mandi-text');
      const prices = data.prices || [];
      if (el && prices.length > 0) {
        const p = prices[0];
        el.textContent = `${p.commodity}: ₹${Number(p.modal_price).toLocaleString('en-IN')}/क्विं`;
        const pill = document.getElementById('hdr-mandi-pill');
        if (pill) {
          pill.style.cursor = 'pointer';
          pill.onclick = () => window.location.href = 'mandi.html';
          pill.title = `${p.commodity} — ₹${Number(p.modal_price).toLocaleString('en-IN')} — पूरे मंडी भाव देखें`;
        }
      }
    } catch (_) {
      const el = document.getElementById('hdr-mandi-text');
      if (el) el.textContent = 'Agmarknet लाइव दरें';
    }
  }

  async function handleLogout() {
    let role = "farmer";
    try {
      if (window.AgriAPI && window.AgriAPI.getMe) {
        const me = await window.AgriAPI.getMe();
        if (me && me.user && me.user.role) role = me.user.role;
      }
      if (window.AgriAPI && window.AgriAPI.logout) {
        await window.AgriAPI.logout();
      }
    } catch (_) {}
    // Explicitly expire client session cookie
    document.cookie = "agrigo_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    try {
      sessionStorage.clear();
      localStorage.removeItem("agrigo_token");
      localStorage.removeItem("agrigo_admin_token");
    } catch (_) {}
    if (role === "admin") {
      window.location.replace("admin-login.html?logged_out=1");
    } else {
      window.location.replace("farmer-login.html?logged_out=1");
    }
  }

  // Auto-inject if data-page attribute is set on <body>
  document.addEventListener('DOMContentLoaded', function () {
    const pg = document.body.getAttribute('data-page');
    if (pg) {
      injectHeader({ page: pg });
    }
  });

  window.AgriHeader = {
    inject: injectHeader,
    handleLogout: handleLogout,
    toggleNotifications: toggleNotifications,
    completeReminderFromNotif: completeReminderFromNotif,
    requestBrowserNotifications: requestBrowserNotifications
  };
})();
