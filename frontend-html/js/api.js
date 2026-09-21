/**
 * AgriGo Centralized API Client (Vanilla JavaScript)
 * Production Session-Based Authentication (HttpOnly Cookies, credentials: 'include')
 * Zero localStorage token storage. Includes date conversion from UTC to local timezone.
 */
const AgriAPI = (() => {
  const isDirectFile = window.location.protocol === "file:";
  const ORIGIN = isDirectFile ? "http://127.0.0.1:8000" : (window.location.origin.includes(":3000") ? "http://127.0.0.1:8000" : "");
  const API_V1 = `${ORIGIN}/api/v1`;

  // Clean up any legacy localStorage auth tokens
  try {
    localStorage.removeItem("agrigo_token");
    localStorage.removeItem("agrigo_admin_token");
  } catch (_) {}

  /**
   * Helper: Convert UTC ISO timestamp to formatted local time string
   * Example output: "20 Sep 2026, 1:34 AM"
   */
  function formatLocalDateTime(utcString) {
    if (!utcString) return "—";
    try {
      // Ensure Z suffix if missing
      const str = utcString.includes("T") && !utcString.endsWith("Z") && !utcString.includes("+") ? utcString + "Z" : utcString;
      const date = new Date(str);
      if (isNaN(date.getTime())) return utcString;
      return date.toLocaleString(undefined, {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true
      });
    } catch (e) {
      return utcString;
    }
  }

  async function request(endpoint, options = {}) {
    // If endpoint starts with /api/, route from root ORIGIN, otherwise append /api/v1
    const url = endpoint.startsWith("/api/") ? `${ORIGIN}${endpoint}` : `${API_V1}${endpoint}`;
    
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || 8000);

    const fetchOptions = {
      ...options,
      headers,
      signal: options.signal || controller.signal,
      credentials: "include" // Send HttpOnly session cookies automatically
    };

    try {
      const response = await fetch(url, fetchOptions);
      clearTimeout(timeoutId);
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        const detailMsg = (errData && typeof errData.detail === "object") ? (errData.detail.message || errData.detail.error) : errData.detail;
        const msg = detailMsg || errData.error || `Request failed (${response.status})`;
        const error = new Error(msg);
        error.status = response.status;
        error.data = errData;
        error.detail = errData.detail;
        throw error;
      }
      return await response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        console.warn(`[AgriAPI Timeout] ${endpoint} exceeded 8s threshold`);
      } else {
        console.error(`[AgriAPI Error] ${endpoint}:`, err);
      }
      throw err;
    }
  }

  return {
    formatLocalDateTime,

    // ----------------- Session Authentication -----------------
    login: (identifier, password, role = "farmer") => request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password, role })
    }),

    logout: () => request("/api/auth/logout", {
      method: "POST"
    }),

    getMe: () => request("/api/auth/me"),

    register: (data) => request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data)
    }),

    // Legacy OTP flow (sets server session cookie on verify)
    requestOTP: (phone) => request("/auth/otp/request", {
      method: "POST",
      body: JSON.stringify({ phone })
    }),

    verifyOTP: (phone, code, logid = null) => request("/auth/otp/verify", {
      method: "POST",
      body: JSON.stringify({ phone, code, ...(logid ? { logid } : {}) })
    }),

    farmerDirectLogin: (identifier, password) => request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password, role: "farmer" })
    }),

    adminLogin: (email, password) => request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier: email, password, role: "admin" })
    }),

    // ----------------- Real Agricultural Weather -----------------
    getAgriWeather: (lat, lon) => {
      const q = (lat !== undefined && lat !== null && lon !== undefined && lon !== null) 
        ? `?lat=${lat}&lon=${lon}` 
        : "";
      return request(`/agriculture/weather${q}`);
    },

    getDetailedWeather: (lat, lon) => {
      const q = (lat !== undefined && lat !== null && lon !== undefined && lon !== null) 
        ? `?lat=${lat}&lon=${lon}` 
        : "";
      return request(`/agriculture/weather/detailed${q}`);
    },

    // ----------------- Mandi Market Prices -----------------
    getMandiPrices: (commodity, state = null, district = null, limit = 50, offset = 0) => {
      let q = `?limit=${limit}&offset=${offset}`;
      if (commodity) q += `&commodity=${encodeURIComponent(commodity)}`;
      if (state && state !== "All") q += `&state=${encodeURIComponent(state)}`;
      if (district) q += `&district=${encodeURIComponent(district)}`;
      return request(`/agriculture/market/live${q}`);
    },

    getMandiMeta: () => request("/agriculture/market/meta"),

    calculateCropRevenue: (payload) => request("/agriculture/market/calculate-revenue", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

    syncLiveMandi: (limit = 500, commodity = null) => {
      let q = `?limit=${limit}`;
      if (commodity) q += `&commodity=${encodeURIComponent(commodity)}`;
      return request(`/agriculture/market/sync${q}`, { method: "POST" });
    },

    // ----------------- Farmer Crops, Reminders & AI Chat -----------------
    getFarmerCrops: (farmerId) => request(`/farmer/crops/${farmerId}`),

    addCropCycle: (data) => request("/farmer/crops", {
      method: "POST",
      body: JSON.stringify(data)
    }),
    
    getFarmerReminders: (farmerId) => request(`/farmer/reminders/${farmerId}`),

    toggleReminder: (reminderId) => request(`/farmer/reminders/${reminderId}/toggle`, {
      method: "PUT"
    }),

    deleteReminder: (reminderId) => request(`/farmer/reminders/${reminderId}`, {
      method: "DELETE"
    }),

    createCustomReminder: (data) => request("/farmer/reminders", {
      method: "POST",
      body: JSON.stringify(data)
    }),

    createNaturalReminder: (text, farmerId) => request("/farmer/reminders/natural", {
      method: "POST",
      body: JSON.stringify({ farmer_id: farmerId, text })
    }),

    askAgriculturalAI: (question, language = "hi", cropContext = null, farmerId = null) => {
      return request("/chat/ask", {
        method: "POST",
        body: JSON.stringify({
          question,
          language,
          crop_context: cropContext,
          farmer_id: farmerId
        })
      });
    },

    uploadLeafImage: async (file) => {
      const formData = new FormData();
      formData.append("file", file);
      const url = `${API_V1}/chat/image`;
      const res = await fetch(url, { method: "POST", body: formData, credentials: "include" });
      return await res.json();
    },

    // ----------------- Secure Admin Control APIs -----------------
    getAdminDashboard: () => request("/api/admin/dashboard"),

    getAdminUsers: (q = "", status = "", role = "") => {
      const params = [];
      if (q) params.push(`q=${encodeURIComponent(q)}`);
      if (status) params.push(`status=${encodeURIComponent(status)}`);
      if (role) params.push(`role=${encodeURIComponent(role)}`);
      const qs = params.length ? `?${params.join("&")}` : "";
      return request(`/api/admin/users${qs}`);
    },

    createAdminUser: (data) => request("/api/admin/users", {
      method: "POST",
      body: JSON.stringify(data)
    }),

    getAdminUserDetail: (userId) => request(`/api/admin/users/${userId}`),

    updateUserStatus: (userId, status) => request(`/api/admin/users/${userId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    }),

    deleteFarmerAccount: (userId) => request(`/api/admin/users/${userId}`, {
      method: "DELETE"
    }),

    getAdminReports: () => request("/api/admin/reports"),

    getAdminAuditLogs: (limit = 50) => request(`/api/admin/audit-logs?limit=${limit}`),

    getAdminHealth: () => request("/api/admin/system/health"),

    getKnowledgeSources: () => request("/api/admin/knowledge-sources"),

    addKnowledgeSource: (data) => request("/api/admin/knowledge-sources", {
      method: "POST",
      body: JSON.stringify(data)
    }),

    deleteKnowledgeSource: (sourceId) => request(`/api/admin/knowledge-sources/${sourceId}`, {
      method: "DELETE"
    }),

    // ----------------- Supabase Cloud DB Direct & Status -----------------
    getSupabaseStatus: () => request("/api/v1/supabase/status"),

    supabaseFetch: async (table, params = "") => {
      const SUPABASE_URL = window.SUPABASE_URL || "";
      const SUPABASE_KEY = window.SUPABASE_KEY || "";
      if (!SUPABASE_URL || !SUPABASE_KEY) {
        return [];
      }
      const url = `${SUPABASE_URL}/rest/v1/${table}${params ? (params.startsWith("?") ? params : "?" + params) : "?select=*"}`;
      const res = await fetch(url, {
        headers: {
          "apikey": SUPABASE_KEY,
          "Authorization": `Bearer ${SUPABASE_KEY}`,
          "Content-Type": "application/json"
        }
      });
      return await res.json();
    },

    // Legacy aliases
    getAdminOverview: () => request("/api/admin/dashboard"),
    getAdminFarmers: () => request("/api/admin/users")
  };
})();
