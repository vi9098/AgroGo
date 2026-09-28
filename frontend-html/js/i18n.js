/**
 * AgriGo Comprehensive Bilingual Translation Engine (Hindi <-> English)
 * Seamless, non-destructive, bidirectional translation for:
 * - Navigation taskbar & headers
 * - Weather Hub metrics & agro-advisories
 * - Mandi Live Rates & Income Calculator
 * - Farmer AI Chat, voice prompts, and sidebar
 * - Reminders & Task manager (Full 30+ Crops & Phenological Stages)
 * - Login, Registration, and Password Reset forms
 * - Privacy Policy, Terms & Conditions, and Cookie Consent
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

    // ── Cookie Notice & Legal ──
    "डेटा सुरक्षा व आवश्यक कुकीज": "Data Privacy & Essential Cookies",
    "गोपनीयता नीति (Privacy Policy)": "Privacy Policy",
    "गोपनीयता नीति": "Privacy Policy",
    "नियम और शर्तें (Terms & Conditions)": "Terms & Conditions",
    "नियम व शर्तें": "Terms & Conditions",
    "कुकी नीति (Cookie Policy)": "Cookie Policy",
    "कुकी नीति": "Cookie Policy",
    "स्वीकार करें": "Accept",
    "स्वीकार करें (Accept)": "Accept",
    "अस्वीकार करें": "Decline",

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

    // ── Reminders Dashboard & Scheduler (Positivus Engine) ──
    "स्वचालित फसल अनुस्मारक": "Automated Crop Reminders",
    "& संपूर्ण प्रबंधन": "& Complete Management",
    "स्वचालित फसल अनुस्मारक\n& संपूर्ण प्रबंधन": "Automated Crop Reminders\n& Complete Management",
    "समय-सारणी बनाएं ➔": "Generate Schedule ➔",
    "+ व्यक्तिगत रिमाइंडर": "+ Custom Reminder",
    "⚡ रीयल-टाइम AI शेड्यूलर": "⚡ Real-time AI Scheduler",
    "🌾 वैज्ञानिक शस्य-विज्ञान (ICAR Package)": "🌾 Scientific Agronomy (ICAR Package)",
    "प्रत्येक फसल की क्रांतिक जल व पोषण अवस्थाओं पर स्वचालित सूचनाएं। बारिश होने पर सिंचाई अनुस्मारक स्वतः पुनर्निर्धारित।": "Automated alerts for critical crop water and nutrition stages. Irrigations reschedule automatically when rain is forecast.",
    "💧 सिंचाई चक्र": "💧 Irrigation Cycles",
    "🌱 खाद खुराक": "🌱 Fertilizer Doses",
    "🛡️ सुरक्षा स्प्रे": "🛡️ Plant Protection",
    "शुरुआती किसान मार्गदर्शन (Beginner Farmer Friendly):": "Beginner Farmer Friendly Guide:",
    "बोलकर या लिखकर बताएं (AI Natural Language Scheduler):": "Speak or Type Sowing Details (AI Natural Language Scheduler):",
    "बहु-फसल (Multi-Crop) समर्थित": "Multi-Crop Supported",
    "🎤 बोलें": "🎤 Speak",
    "बोलें": "Speak",
    "⚡ AI से तुरंत कैलेंडर बनाएं ➔": "⚡ Generate AI Calendar ➔",
    "त्वरित उदाहरण:": "Quick Examples:",
    "अथवा नीचे विवरण चुनकर बनाएं": "Or Choose Details Below",
    "01 मिनट में तैयार": "Ready in 1 Minute",
    "🌾 अपनी फसल व एकड़ का चयन करें": "🌾 Select Crop & Acreage",
    "एकड़ के हिसाब से खाद की मात्रा और तारीखें स्वतः परिकलित होंगी।": "Fertilizer quantities and task dates are calculated accurately by acreage.",
    "इंजन:": "Engine:",
    "🌾 फसल का नाम (Crop Name)": "🌾 Crop Name",
    "📅 बुवाई / रोपाई की तारीख (Sowing Date)": "📅 Sowing / Planting Date",
    "🚜 खेत का रकबा / क्षेत्रफल (Acres)": "🚜 Farm Land Area (Acres)",
    "एकड़ (Acres)": "Acres",
    "📍 आज (Today)": "📍 Today",
    "⏮️ 7 दिन पूर्व": "⏮️ 7 Days Ago",
    "⏮️ 15 दिन पूर्व": "⏮️ 15 Days Ago",
    "1 एकड़": "1 Acre",
    "2 एकड़": "2 Acres",
    "3 एकड़": "3 Acres",
    "5 एकड़": "5 Acres",
    "⚡ संपूर्ण फसल कैलेंडर व अनुस्मारक तैयार करें ➔": "⚡ Generate Full Crop Calendar & Reminders ➔",
    "📋 फसल जीवन-चक्र चरण (Crop Lifecycle & Process)": "📋 Crop Lifecycle & Phenological Process",
    "सभी चरण विस्तार करें": "Expand All Stages",
    "सभी कार्य": "All Tasks",
    "💧 सिंचाई": "💧 Irrigation",
    "🌱 खाद व पोषण": "🌱 Fertilizer & Nutrients",
    "🛡️ पादप सुरक्षा": "🛡️ Plant Protection",
    "✓ पूर्ण": "✓ Completed",
    "सिंचाई": "Irrigation",
    "पादप सुरक्षा": "Plant Protection",
    "खाद व पोषण": "Fertilizer & Nutrients",
    "देय:": "Due:",
    "शीघ्र": "Upcoming",
    "आज ही देय": "Due Today",
    "कल देय": "Due Tomorrow",
    "दिन पूर्व": "days ago",
    "दिन शेष": "days left",
    "✓ पूर्ण": "✓ Done",
    "↺ सक्रिय": "↺ Active",
    "कार्य संलग्न": "tasks attached",
    "📋 इस चरण के अंतर्गत आने वाले वैज्ञानिक कार्य:": "📋 Scientific tasks for this stage:",
    "इस चरण में कोई लंबित कार्य नहीं है।": "No pending tasks in this stage.",
    "कृषि अनुस्मारक": "Agri Reminders",
    "लंबित कार्य": "Pending Tasks",
    "पूर्ण कार्य": "Completed Tasks",
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
    "खुदाई / निराई": "Weeding & Hoeing",
    "खुराक:": "Dosage:",
    "कटाई": "Harvest",
    "परिपक्वता": "Maturity",

    // ── 30+ Crops Names (Bilingual Match) ──
    "-- 30+ वैज्ञानिक फसलों में से चुनें (Select Crop) --": "-- Select from 30+ Scientific Crops --",
    "🌾 अनाज व मोटे अनाज (Cereals & Millets)": "🌾 Cereals & Millets",
    "🫘 दलहनी फसलें (Pulses & Legumes)": "🫘 Pulses & Legumes",
    "🌻 तिलहनी फसलें (Oilseeds)": "🌻 Oilseeds",
    "🎋 नकदी व रेशेदार फसलें (Cash & Fiber)": "🎋 Cash & Fiber",
    "🥔 सब्जियां (Vegetables)": "🥔 Vegetables",
    "🌿 मसाले (Spices & Condiments)": "🌿 Spices & Condiments",
    "🍉 फल (Fruits)": "🍉 Fruits",
    "✏️ अन्य फसल (Type Custom)...": "✏️ Other Crop (Type Custom)...",
    "🌾 गेहूं (Wheat)": "🌾 Wheat",
    "🌾 धान (Paddy / Rice)": "🌾 Paddy / Rice",
    "🌽 मक्का (Maize)": "🌽 Maize",
    "🌾 बाजरा (Pearl Millet)": "🌾 Pearl Millet (Bajra)",
    "🌾 ज्वार (Sorghum / Jowar)": "🌾 Sorghum (Jowar)",
    "🌾 जौ (Barley)": "🌾 Barley (Jau)",
    "🫘 चना (Gram / Chickpea)": "🫘 Chickpea (Gram)",
    "🫘 अरहर (Pigeon Pea / Arhar)": "🫘 Pigeon Pea (Arhar/Tur)",
    "🟢 मूंग (Green Gram / Moong)": "🟢 Green Gram (Moong)",
    "⚫ उड़द (Black Gram / Urad)": "⚫ Black Gram (Urad)",
    "🟢 मटर (Green Pea)": "🟢 Green Pea (Matar)",
    "🫘 मसूर (Lentil / Masoor)": "🫘 Lentil (Masoor)",
    "🌼 सरसों (Mustard)": "🌼 Mustard (Sarson)",
    "🌱 सोयाबीन (Soybean)": "🌱 Soybean",
    "🥜 मूंगफली (Groundnut)": "🥜 Groundnut (Peanut)",
    "🌻 सूरजमुखी (Sunflower)": "🌻 Sunflower",
    "☁️ कपास (Cotton)": "☁️ Cotton",
    "🎋 गन्ना (Sugarcane)": "🎋 Sugarcane",
    "🥔 आलू (Potato)": "🥔 Potato",
    "🍅 टमाटर (Tomato)": "🍅 Tomato",
    "🧅 प्याज (Onion)": "🧅 Onion",
    "🧄 लहसुन (Garlic)": "🧄 Garlic",
    "🌶️ मिर्च (Chilli)": "🌶️ Chilli",
    "🍆 बैंगन (Brinjal)": "🍆 Brinjal (Eggplant)",
    "🥦 फूलगोभी (Cauliflower)": "🥦 Cauliflower",
    "🥬 पत्तागोभी (Cabbage)": "🥬 Cabbage",
    "🥬 भिंडी (Okra)": "🥬 Okra (Bhindi)",
    "🫚 अदरक (Ginger)": "🫚 Ginger",
    "🟡 हल्दी (Turmeric)": "🟡 Turmeric",
    "🟤 जीरा (Cumin / Jeera)": "🟤 Cumin (Jeera)",
    "🌿 धनिया (Coriander)": "🌿 Coriander (Dhaniya)",
    "🍉 तरबूज (Watermelon)": "🍉 Watermelon",

    // ── Quick Chips ──
    "🌼 सरसों": "🌼 Mustard",
    "🌾 गेहूं": "🌾 Wheat",
    "🫘 चना": "🫘 Gram",
    "🧄 लहसुन": "🧄 Garlic",
    "🧅 प्याज": "🧅 Onion",
    "🌶️ मिर्च": "🌶️ Chilli",
    "🍅 टमाटर": "🍅 Tomato",
    "🥔 आलू": "🥔 Potato",
    "🌾 3 एकड़ गेहूं आज": "🌾 3 Acres Wheat Today",
    "🌾+🌼 गेहूं 3 एकड़ व सरसों 2 एकड़": "🌾+🌼 Wheat 3 Ac & Mustard 2 Ac",
    "🍅 1.5 एकड़ टमाटर": "🍅 1.5 Acres Tomato",
    "💧 कल गेहूं में पानी": "💧 Irrigate Wheat Tomorrow",

    // ── Stages ──
    "बुवाई व आधार खाद चरण (Basal & Sowing Stage)": "Basal & Sowing Stage",
    "वानस्पतिक व कल्ले फूटने का चरण (Vegetative & Tillering Stage)": "Vegetative & Tillering Stage",
    "गाभा व फूल आने का क्रांतिक चरण (Booting & Flowering Stage)": "Booting & Flowering Stage",
    "दाना भराव व दुग्ध अवस्था (Grain Filling & Milking Stage)": "Grain Filling & Milking Stage",
    "परिपक्वता व कटाई चरण (Maturity & Harvesting Stage)": "Maturity & Harvesting Stage",
    "बुवाई के 0-15 दिन": "0-15 Days from Sowing",
    "बुवाई के 16-45 दिन": "16-45 Days from Sowing",
    "बुवाई के 46-75 दिन": "46-75 Days from Sowing",
    "बुवाई के 76-105 दिन": "76-105 Days from Sowing",
    "बुवाई के 106-140 दिन": "106-140 Days from Sowing",

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

    // ── Registration & Login ──
    "नमस्ते किसान भाई!": "Welcome Farmer!",
    "अपने पंजीकृत मोबाइल नंबर से प्रवेश करें": "Enter using your registered mobile number",
    "किसान लॉगिन • Farmer Login": "Farmer Login",
    "मोबाइल नंबर (Mobile Number)": "Mobile Number",
    "पासवर्ड (Password)": "Password",
    "अपना पासवर्ड दर्ज करें": "Enter your password",
    "🔑 पासवर्ड भूल गए? (Forgot Password?)": "🔑 Forgot Password?",
    "खेत में प्रवेश करें ➔": "Enter Dashboard ➔",
    "🌱 नया पंजीकरण (Register)": "🌱 New Registration",
    "🏠 मुख्य पृष्ठ (Home)": "🏠 Home",
    "नया किसान पंजीकरण": "New Farmer Registration",
    "पूरा नाम": "Full Name",
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
    // Normalize: 'hi' is Hindi, 'en' is English; other regional scripts cleanly fall back to English if requested
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

    // Notify listeners across app (e.g. reminders.js, mandi.js, farmer.js, weather.js)
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

      // Cache original text on node
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
            if (hiStr.length >= 3 && node.nodeValue.includes(hiStr)) {
              node.nodeValue = node.nodeValue.split(hiStr).join(enStr);
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
          let updated = orig;
          for (const [hiStr, enStr] of Object.entries(DICT)) {
            if (hiStr.length >= 3 && updated.includes(hiStr)) {
              updated = updated.split(hiStr).join(enStr);
            }
          }
          input.setAttribute("placeholder", updated);
        }
      }
    });

    // 4. Translate Select Options & Optgroups
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
        } else {
          let updated = orig;
          for (const [hiStr, enStr] of Object.entries(DICT)) {
            if (hiStr.length >= 3 && updated.includes(hiStr)) {
              updated = updated.split(hiStr).join(enStr);
            }
          }
          opt.textContent = updated;
        }
      }
    });

    rootNode.querySelectorAll("select optgroup").forEach(grp => {
      const label = grp.getAttribute("label");
      if (!label) return;
      if (!grp.dataset.origLabel) {
        grp.dataset.origLabel = label;
      }
      if (isHindi) {
        grp.setAttribute("label", grp.dataset.origLabel);
      } else {
        const orig = grp.dataset.origLabel;
        if (DICT[orig]) {
          grp.setAttribute("label", DICT[orig]);
        }
      }
    });

    // 5. Translate Titles & Aria-Labels for Accessibility
    rootNode.querySelectorAll("[title]").forEach(el => {
      const t = el.getAttribute("title");
      if (!t) return;
      if (!el.dataset.origTitle) el.dataset.origTitle = t;
      if (isHindi) {
        el.setAttribute("title", el.dataset.origTitle);
      } else {
        const orig = el.dataset.origTitle;
        if (DICT[orig]) el.setAttribute("title", DICT[orig]);
      }
    });
  }

  // Auto MutationObserver for dynamically injected elements when in English mode
  let translationTimeout = null;
  function observeDynamicContent() {
    const observer = new MutationObserver((mutations) => {
      if (getLanguage() === "hi") return;
      let shouldTranslate = false;
      for (const m of mutations) {
        if (m.addedNodes.length > 0) {
          shouldTranslate = true;
          break;
        }
      }
      if (shouldTranslate) {
        clearTimeout(translationTimeout);
        translationTimeout = setTimeout(() => {
          applyTranslation(getLanguage() === "hi" ? "hi" : "en");
        }, 80);
      }
    });

    if (document.body) {
      observer.observe(document.body, { childList: true, subtree: true });
    }
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

    observeDynamicContent();
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
