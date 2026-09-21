/**
 * Gateway Interactions: Tab switching, OTP Handling, and Production Session Logins
 * Zero localStorage token storage. Relies entirely on server-side session cookies.
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Dismiss loading overlay smoothly
  setTimeout(() => {
    const loader = document.getElementById("loading-overlay");
    if (loader) loader.classList.add("hidden");
  }, 400);

  // Note: No automatic redirect on home page load; user remains on home page

  // Fetch quick weather indicator
  try {
    const weather = await AgriAPI.getAgriWeather();
    const wBadge = document.getElementById("weather-badge");
    if (wBadge && weather) {
      wBadge.innerText = `🌤️ ${weather.temperature_c}°C | बारिश: ${weather.rain_prob_today_pct}%`;
    }
  } catch (e) {
    console.log("Weather preview not available:", e);
  }
});

function switchFarmerTab(tab) {
  const otpSec = document.getElementById("farmer-otp-section");
  const passSec = document.getElementById("farmer-pass-section");
  const tabOtp = document.getElementById("tab-otp");
  const tabPass = document.getElementById("tab-pass");

  if (tab === 'otp') {
    otpSec.style.display = "block";
    passSec.style.display = "none";
    tabOtp.className = "btn btn-secondary";
    tabPass.className = "btn btn-outline";
  } else {
    otpSec.style.display = "none";
    passSec.style.display = "block";
    tabOtp.className = "btn btn-outline";
    tabPass.className = "btn btn-secondary";
  }
}

let otpTimerInterval = null;
let lastOtpLogId = null;

async function handleRequestOTP() {
  const phone = document.getElementById("farmer-phone").value.trim();
  if (!phone || phone.replace(/\D/g, '').length < 10) {
    alert("कृपया सही 10-अंकों का मोबाइल नंबर दर्ज करें।");
    return;
  }

  const reqBtn = document.getElementById("btn-request-otp");
  reqBtn.innerText = "भेज रहे हैं...";
  reqBtn.disabled = true;

  try {
    const data = await AgriAPI.requestOTP(phone);
    if (data && data.logid) {
      lastOtpLogId = data.logid;
    }

    // Show dynamic SMS dispatch status banner
    const banner = document.getElementById("otp-sent-banner");
    const bannerTitle = document.getElementById("otp-sent-title");
    const bannerDesc = document.getElementById("otp-sent-desc");
    
    if (banner) {
      banner.style.display = "block";
      const masked = data.phone_masked || `+91-XXXXXX${phone.slice(-4)}`;
      if (bannerTitle) bannerTitle.innerText = `OTP ${masked} पर भेज दिया गया है`;
      if (bannerDesc) {
        if (data.dispatched) {
          bannerDesc.innerText = "Authkey.io SMS गेटवे द्वारा आपके मोबाइल पर 6-अंकों का कोड भेज दिया गया है।";
        } else {
          bannerDesc.innerText = "कृपया अपने मोबाइल के SMS इनबॉक्स में प्राप्त 6-अंकों का सत्यापन कोड नीचे दर्ज करें।";
        }
      }
    }

    // Reveal OTP input and verification button (DO NOT auto-fill)
    const inputGroup = document.getElementById("otp-input-group");
    const verifyBtn = document.getElementById("btn-verify-otp");
    const otpInput = document.getElementById("farmer-otp-input");

    if (inputGroup) inputGroup.style.display = "block";
    if (verifyBtn) verifyBtn.style.display = "block";
    if (otpInput) {
      otpInput.value = "";
      otpInput.focus();
    }

    // Cooldown timer: 60 seconds before allowing resend
    if (otpTimerInterval) clearInterval(otpTimerInterval);
    let countdown = 60;
    const timerSpan = document.getElementById("otp-timer");

    reqBtn.innerText = `OTP भेजा गया (${countdown}s)`;
    otpTimerInterval = setInterval(() => {
      countdown--;
      if (countdown > 0) {
        reqBtn.innerText = `पुनः भेजें (${countdown}s)`;
        if (timerSpan) timerSpan.innerText = `पुनः भेजें: ${countdown}s में`;
      } else {
        clearInterval(otpTimerInterval);
        reqBtn.innerText = "OTP पुनः भेजें";
        reqBtn.disabled = false;
        if (timerSpan) timerSpan.innerText = "OTP प्राप्त नहीं हुआ? पुनः भेजें";
      }
    }, 1000);

  } catch (err) {
    alert("OTP भेजने में त्रुटि: " + (err.message || err));
    reqBtn.innerText = "OTP भेजें";
    reqBtn.disabled = false;
  }
}

async function handleVerifyOTP() {
  const phone = document.getElementById("farmer-phone").value.trim();
  const code = document.getElementById("farmer-otp-input").value.trim();

  if (!code || code.length !== 6 || !/^\d{6}$/.test(code)) {
    alert("कृपया 6-अंकों का मान्य संख्यात्मक OTP कोड दर्ज करें।");
    return;
  }

  const verifyBtn = document.getElementById("btn-verify-otp");
  verifyBtn.innerText = "सत्यापित हो रहा है...";
  verifyBtn.disabled = true;

  try {
    await AgriAPI.verifyOTP(phone, code, lastOtpLogId);
    // Server establishes secure HttpOnly session cookie
    window.location.href = "farmer.html";
  } catch (err) {
    alert("OTP सत्यापन विफल: " + (err.message || "अमान्य अथवा समाप्त OTP कोड दर्ज किया गया है।"));
    verifyBtn.innerText = "सत्यापित करें और प्रवेश करें ➔";
    verifyBtn.disabled = false;
  }
}

async function handleFarmerPasswordLogin() {
  const id = document.getElementById("farmer-id-input").value.trim();
  const pass = document.getElementById("farmer-password-input").value.trim();

  try {
    await AgriAPI.farmerDirectLogin(id, pass);
    // Server has established HttpOnly session cookie
    window.location.href = "farmer.html";
  } catch (err) {
    alert("किसान लॉगिन त्रुटि: " + err.message);
  }
}

async function handleAdminLogin() {
  const email = document.getElementById("admin-email").value.trim();
  const pass = document.getElementById("admin-pass").value.trim();

  try {
    await AgriAPI.adminLogin(email, pass);
    // Server has established HttpOnly session cookie
    window.location.href = "admin.html";
  } catch (err) {
    alert("एडमिन लॉगिन त्रुटि: " + err.message);
  }
}
