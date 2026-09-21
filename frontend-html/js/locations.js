/**
 * AgriGo Comprehensive Indian States & Agricultural Districts Geographic Registry
 * Covers all 28 States and 8 Union Territories of India with geographic coordinates.
 * Provides cascading State -> District selection and flexible bilingual resolution.
 */

const INDIA_LOCATIONS = {
  // ----------------- 28 STATES -----------------
  "उत्तर प्रदेश (Uttar Pradesh)": {
    "वाराणसी (Varanasi)": { lat: 25.3176, lon: 82.9739, name: "वाराणसी, उत्तर प्रदेश" },
    "लखनऊ (Lucknow)": { lat: 26.8467, lon: 80.9462, name: "लखनऊ, उत्तर प्रदेश" },
    "कानपुर (Kanpur)": { lat: 26.4499, lon: 80.3319, name: "कानपुर, उत्तर प्रदेश" },
    "प्रयागराज (Prayagraj)": { lat: 25.4358, lon: 81.8463, name: "प्रयागराज, उत्तर प्रदेश" },
    "गोरखपुर (Gorakhpur)": { lat: 26.7606, lon: 83.3732, name: "गोरखपुर, उत्तर प्रदेश" },
    "आगरा (Agra)": { lat: 27.1767, lon: 78.0081, name: "आगरा, उत्तर प्रदेश" },
    "मेरठ (Meerut)": { lat: 28.9845, lon: 77.7064, name: "मेरठ, उत्तर प्रदेश" },
    "बरेली (Bareilly)": { lat: 28.3670, lon: 79.4304, name: "बरेली, उत्तर प्रदेश" },
    "अलीगढ़ (Aligarh)": { lat: 27.8974, lon: 78.0880, name: "अलीगढ़, उत्तर प्रदेश" },
    "मुरादाबाद (Moradabad)": { lat: 28.8389, lon: 78.7768, name: "मुरादाबाद, उत्तर प्रदेश" },
    "अयोध्या (Ayodhya)": { lat: 26.7922, lon: 82.1998, name: "अयोध्या, उत्तर प्रदेश" },
    "झांसी (Jhansi)": { lat: 25.4484, lon: 78.5685, name: "झांसी, उत्तर प्रदेश" },
    "मुजफ्फरनगर (Muzaffarnagar)": { lat: 29.4727, lon: 77.7085, name: "मुजफ्फरनगर, उत्तर प्रदेश" },
    "बुलंदशहर (Bulandshahr)": { lat: 28.4069, lon: 77.8498, name: "बुलंदशहर, उत्तर प्रदेश" },
    "गाजीपुर (Ghazipur)": { lat: 25.5866, lon: 83.5770, name: "गाजीपुर, उत्तर प्रदेश" },
    "मथुरा (Mathura)": { lat: 27.4924, lon: 77.6737, name: "मथुरा, उत्तर प्रदेश" },
    "सहारनपुर (Saharanpur)": { lat: 29.9671, lon: 77.5510, name: "सहारनपुर, उत्तर प्रदेश" },
    "मिर्जापुर (Mirzapur)": { lat: 25.1337, lon: 82.5644, name: "मिर्जापुर, उत्तर प्रदेश" },
    "जौनपुर (Jaunpur)": { lat: 25.7464, lon: 82.6837, name: "जौनपुर, उत्तर प्रदेश" },
    "बस्ती (Basti)": { lat: 26.8066, lon: 82.7667, name: "बस्ती, उत्तर प्रदेश" },
    "आजमगढ़ (Azamgarh)": { lat: 26.0738, lon: 83.1859, name: "आजमगढ़, उत्तर प्रदेश" },
    "बलिया (Ballia)": { lat: 25.7588, lon: 84.1481, name: "बलिया, उत्तर प्रदेश" }
  },
  "पंजाब (Punjab)": {
    "बठिंडा (Bathinda)": { lat: 30.2110, lon: 74.9455, name: "बठिंडा, पंजाब" },
    "लुधियाना (Ludhiana)": { lat: 30.9010, lon: 75.8573, name: "लुधियाना, पंजाब" },
    "अमृतसर (Amritsar)": { lat: 31.6340, lon: 74.8723, name: "अमृतसर, पंजाब" },
    "जालंधर (Jalandhar)": { lat: 31.3260, lon: 75.5762, name: "जालंधर, पंजाब" },
    "पटियाला (Patiala)": { lat: 30.3398, lon: 76.3869, name: "पटियाला, पंजाब" },
    "संगरूर (Sangrur)": { lat: 30.2458, lon: 75.8420, name: "संगरूर, पंजाब" },
    "फिरोजपुर (Firozpur)": { lat: 30.9237, lon: 74.6115, name: "फिरोजपुर, पंजाब" },
    "होशियारपुर (Hoshiarpur)": { lat: 31.5273, lon: 75.9149, name: "होशियारपुर, पंजाब" },
    "गुरदासपुर (Gurdaspur)": { lat: 32.0419, lon: 75.4053, name: "गुरदासपुर, पंजाब" },
    "मानसा (Mansa)": { lat: 29.9888, lon: 75.3934, name: "मानसा, पंजाब" },
    "मोगा (Moga)": { lat: 30.8165, lon: 75.1717, name: "मोगा, पंजाब" },
    "मुक्तसर (Muktsar)": { lat: 30.4762, lon: 74.5170, name: "मुक्तसर, पंजाब" }
  },
  "हरियाणा (Haryana)": {
    "करनाल (Karnal)": { lat: 29.6857, lon: 76.9905, name: "करनाल, हरियाणा" },
    "हिसार (Hisar)": { lat: 29.1492, lon: 75.7217, name: "हिसार, हरियाणा" },
    "अंबाला (Ambala)": { lat: 30.3782, lon: 76.7767, name: "अंबाला, हरियाणा" },
    "रोहतक (Rohtak)": { lat: 28.8955, lon: 76.6066, name: "रोहतक, हरियाणा" },
    "सिरसा (Sirsa)": { lat: 29.5349, lon: 75.0296, name: "सिरसा, हरियाणा" },
    "कुरुक्षेत्र (Kurukshetra)": { lat: 29.9695, lon: 76.8783, name: "कुरुक्षेत्र, हरियाणा" },
    "सोनीपत (Sonipat)": { lat: 28.9931, lon: 77.0151, name: "सोनीपत, हरियाणा" },
    "पानीपत (Panipat)": { lat: 29.3909, lon: 76.9635, name: "पानीपत, हरियाणा" },
    "फतेहाबाद (Fatehabad)": { lat: 29.5140, lon: 75.4544, name: "फतेहाबाद, हरियाणा" },
    "जींद (Jind)": { lat: 29.3160, lon: 76.3197, name: "जींद, हरियाणा" },
    "यमुनानगर (Yamunanagar)": { lat: 30.1290, lon: 77.2674, name: "यमुनानगर, हरियाणा" }
  },
  "मध्य प्रदेश (Madhya Pradesh)": {
    "इंदौर (Indore)": { lat: 22.7196, lon: 75.8577, name: "इंदौर, मध्य प्रदेश" },
    "भोपाल (Bhopal)": { lat: 23.2599, lon: 77.4126, name: "भोपाल, मध्य प्रदेश" },
    "उज्जैन (Ujjain)": { lat: 23.1765, lon: 75.7885, name: "उज्जैन, मध्य प्रदेश" },
    "जबलपुर (Jabalpur)": { lat: 23.1815, lon: 79.9864, name: "जबलपुर, मध्य प्रदेश" },
    "ग्वालियर (Gwalior)": { lat: 26.2183, lon: 78.1828, name: "ग्वालियर, मध्य प्रदेश" },
    "नर्मदापुरम (Narmadapuram / Hoshangabad)": { lat: 22.7519, lon: 77.7289, name: "नर्मदापुरम, मध्य प्रदेश" },
    "सीहोर (Sehore)": { lat: 23.2030, lon: 77.0844, name: "सीहोर, मध्य प्रदेश" },
    "धार (Dhar)": { lat: 22.5982, lon: 75.2974, name: "धार, मध्य प्रदेश" },
    "नीमच (Neemuch)": { lat: 24.4727, lon: 74.8727, name: "नीमच, मध्य प्रदेश" },
    "मंदसौर (Mandsaur)": { lat: 24.0722, lon: 75.0694, name: "मंदसौर, मध्य प्रदेश" },
    "रतलाम (Ratlam)": { lat: 23.3341, lon: 75.0376, name: "रतलाम, मध्य प्रदेश" },
    "खरगोन (Khargone)": { lat: 21.8234, lon: 75.6186, name: "खरगोन, मध्य प्रदेश" },
    "विदिशा (Vidisha)": { lat: 23.5251, lon: 77.8081, name: "विदिशा, मध्य प्रदेश" }
  },
  "महाराष्ट्र (Maharashtra)": {
    "नासिक (Nashik)": { lat: 19.9975, lon: 73.7898, name: "नासिक, महाराष्ट्र" },
    "पुणे (Pune)": { lat: 18.5204, lon: 73.8567, name: "पुणे, महाराष्ट्र" },
    "नागपुर (Nagpur)": { lat: 21.1458, lon: 79.0882, name: "नागपुर, महाराष्ट्र" },
    "छत्रपति संभाजीनगर (Aurangabad)": { lat: 19.8762, lon: 75.3433, name: "छत्रपति संभाजीनगर, महाराष्ट्र" },
    "सोलापुर (Solapur)": { lat: 17.6599, lon: 75.9064, name: "सोलापुर, महाराष्ट्र" },
    "कोल्हापुर (Kolhapur)": { lat: 16.7050, lon: 74.2433, name: "कोल्हापुर, महाराष्ट्र" },
    "अमरावती (Amravati)": { lat: 20.9320, lon: 77.7523, name: "अमरावती, महाराष्ट्र" },
    "जलगांव (Jalgaon)": { lat: 21.0077, lon: 75.5626, name: "जलगांव, महाराष्ट्र" },
    "अकोला (Akola)": { lat: 20.7002, lon: 77.0082, name: "अकोला, महाराष्ट्र" },
    "अहमदनगर (Ahmednagar)": { lat: 19.0948, lon: 74.7479, name: "अहमदनगर, महाराष्ट्र" },
    "लातूर (Latur)": { lat: 18.4088, lon: 76.5604, name: "लातूर, महाराष्ट्र" },
    "सांगली (Sangli)": { lat: 16.8524, lon: 74.5815, name: "सांगली, महाराष्ट्र" },
    "नांदेड़ (Nanded)": { lat: 19.1383, lon: 77.3210, name: "नांदेड़, महाराष्ट्र" },
    "यवतमाल (Yavatmal)": { lat: 20.3888, lon: 78.1204, name: "यवतमाल, महाराष्ट्र" }
  },
  "राजस्थान (Rajasthan)": {
    "जयपुर (Jaipur)": { lat: 26.9124, lon: 75.7873, name: "जयपुर, राजस्थान" },
    "जोधपुर (Jodhpur)": { lat: 26.2389, lon: 73.0243, name: "जोधपुर, राजस्थान" },
    "कोटा (Kota)": { lat: 25.2138, lon: 75.8648, name: "कोटा, राजस्थान" },
    "उदयपुर (Udaipur)": { lat: 24.5854, lon: 73.7125, name: "उदयपुर, राजस्थान" },
    "बीकानेर (Bikaner)": { lat: 28.0229, lon: 73.3119, name: "बीकानेर, राजस्थान" },
    "श्रीगंगानगर (Sri Ganganagar)": { lat: 29.9038, lon: 73.8772, name: "श्रीगंगानगर, राजस्थान" },
    "अलवर (Alwar)": { lat: 27.5530, lon: 76.6346, name: "अलवर, राजस्थान" },
    "भरतपुर (Bharatpur)": { lat: 27.2152, lon: 77.5030, name: "भरतपुर, राजस्थान" },
    "हनुमानगढ़ (Hanumangarh)": { lat: 29.5810, lon: 74.3294, name: "हनुमानगढ़, राजस्थान" },
    "नागौर (Nagaur)": { lat: 27.2021, lon: 73.7439, name: "नागौर, राजस्थान" },
    "अजमेर (Ajmer)": { lat: 26.4499, lon: 74.6399, name: "अजमेर, राजस्थान" },
    "बारां (Baran)": { lat: 25.1011, lon: 76.5132, name: "बारां, राजस्थान" }
  },
  "गुजरात (Gujarat)": {
    "अहमदाबाद (Ahmedabad)": { lat: 23.0225, lon: 72.5714, name: "अहमदाबाद, गुजरात" },
    "सूरत (Surat)": { lat: 21.1702, lon: 72.8311, name: "सूरत, गुजरात" },
    "राजकोट (Rajkot)": { lat: 22.3039, lon: 70.8022, name: "राजकोट, गुजरात" },
    "वडोदरा (Vadodara)": { lat: 22.3072, lon: 73.1812, name: "वडोदरा, गुजरात" },
    "जूनागढ़ (Junagadh)": { lat: 21.5222, lon: 70.4579, name: "जूनागढ़, गुजरात" },
    "मेहसाणा (Mehsana)": { lat: 23.5880, lon: 72.3693, name: "मेहसाणा, गुजरात" },
    "आनंद (Anand)": { lat: 22.5645, lon: 72.9289, name: "आनंद, गुजरात" },
    "भावनगर (Bhavnagar)": { lat: 21.7645, lon: 72.1519, name: "भावनगर, गुजरात" },
    "जामनगर (Jamnagar)": { lat: 22.4707, lon: 70.0577, name: "जामनगर, गुजरात" },
    "अमरेली (Amreli)": { lat: 21.6032, lon: 71.2221, name: "अमरेली, गुजरात" },
    "बनासकांठा (Banaskantha / Palanpur)": { lat: 24.1724, lon: 72.4346, name: "बनासकांठा, गुजरात" }
  },
  "बिहार (Bihar)": {
    "पटना (Patna)": { lat: 25.5941, lon: 85.1376, name: "पटना, बिहार" },
    "मुजफ्फरपुर (Muzaffarpur)": { lat: 26.1209, lon: 85.3647, name: "मुजफ्फरपुर, बिहार" },
    "गया (Gaya)": { lat: 24.7914, lon: 85.0002, name: "गया, बिहार" },
    "भागलपुर (Bhagalpur)": { lat: 25.2425, lon: 86.9842, name: "भागलपुर, बिहार" },
    "दरभंगा (Darbhanga)": { lat: 26.1542, lon: 85.8918, name: "दरभंगा, बिहार" },
    "समस्तीपुर (Samastipur)": { lat: 25.8560, lon: 85.7868, name: "समस्तीपुर, बिहार" },
    "रोहतास (Rohtas / Sasaram)": { lat: 24.9528, lon: 84.0150, name: "रोहतास, बिहार" },
    "पश्चिम चंपारण (West Champaran)": { lat: 27.1565, lon: 84.4447, name: "पश्चिम चंपारण, बिहार" },
    "बेगूसराय (Begusarai)": { lat: 25.4182, lon: 86.1272, name: "बेगूसराय, बिहार" },
    "नालंदा (Nalanda / Bihar Sharif)": { lat: 25.1983, lon: 85.5149, name: "नालंदा, बिहार" },
    "पूर्णिया (Purnia)": { lat: 25.7771, lon: 87.4753, name: "पूर्णिया, बिहार" }
  },
  "पश्चिम बंगाल (West Bengal)": {
    "कोलकाता (Kolkata)": { lat: 22.5726, lon: 88.3639, name: "कोलकाता, पश्चिम बंगाल" },
    "बर्दवान (Bardhaman / Purba Bardhaman)": { lat: 23.2324, lon: 87.8615, name: "बर्दवान, पश्चिम बंगाल" },
    "हुगली (Hooghly)": { lat: 22.8963, lon: 88.2461, name: "हुगली, पश्चिम बंगाल" },
    "मुर्शिदाबाद (Murshidabad)": { lat: 24.1759, lon: 88.2802, name: "मुर्शिदाबाद, पश्चिम बंगाल" },
    "नादिया (Nadia)": { lat: 23.4710, lon: 88.5565, name: "नादिया, पश्चिम बंगाल" },
    "उत्तर 24 परगना (North 24 Parganas)": { lat: 22.7230, lon: 88.4807, name: "उत्तर 24 परगना, पश्चिम बंगाल" },
    "मालदा (Malda)": { lat: 25.0108, lon: 88.1411, name: "मालदा, पश्चिम बंगाल" },
    "जलपाईगुड़ी (Jalpaiguri)": { lat: 26.5422, lon: 88.7179, name: "जलपाईगुड़ी, पश्चिम बंगाल" }
  },
  "कर्नाटक (Karnataka)": {
    "बेंगलुरु (Bengaluru)": { lat: 12.9716, lon: 77.5946, name: "बेंगलुरु, कर्नाटक" },
    "मैसूर (Mysuru)": { lat: 12.2958, lon: 76.6394, name: "मैसूर, कर्नाटक" },
    "बेलगावी (Belagavi)": { lat: 15.8497, lon: 74.4977, name: "बेलगावी, कर्नाटक" },
    "धारवाड़ (Dharwad)": { lat: 15.4589, lon: 75.0078, name: "धारवाड़, कर्नाटक" },
    "शिवमोग्गा (Shivamogga)": { lat: 13.9299, lon: 75.5681, name: "शिवमोग्गा, कर्नाटक" },
    "कोलार (Kolar)": { lat: 13.1367, lon: 78.1291, name: "कोलार, कर्नाटक" },
    "हावेरी (Haveri)": { lat: 14.7954, lon: 75.3991, name: "हावेरी, कर्नाटक" },
    "दावणगेरे (Davanagere)": { lat: 14.4644, lon: 75.9218, name: "दावणगेरे, कर्नाटक" },
    "कलबुर्गी (Kalaburagi / Gulbarga)": { lat: 17.3297, lon: 76.8343, name: "कलबुर्गी, कर्नाटक" },
    "विजयपुरा (Vijayapura / Bijapur)": { lat: 16.8302, lon: 75.7100, name: "विजयपुरा, कर्नाटक" }
  },
  "आंध्र प्रदेश (Andhra Pradesh)": {
    "विजयवाड़ा (Vijayawada)": { lat: 16.5062, lon: 80.6480, name: "विजयवाड़ा, आंध्र प्रदेश" },
    "गुंटूर (Guntur)": { lat: 16.3067, lon: 80.4365, name: "गुंटूर, आंध्र प्रदेश" },
    "कर्नूल (Kurnool)": { lat: 15.8281, lon: 78.0373, name: "कर्नूल, आंध्र प्रदेश" },
    "विशाखापत्तनम (Visakhapatnam)": { lat: 17.6868, lon: 83.2185, name: "विशाखापत्तनम, आंध्र प्रदेश" },
    "अनंतपुर (Anantapur)": { lat: 14.6819, lon: 77.6006, name: "अनंतपुर, आंध्र प्रदेश" },
    "पूर्वी गोदावरी (East Godavari / Rajahmundry)": { lat: 17.0005, lon: 81.8040, name: "पूर्वी गोदावरी, आंध्र प्रदेश" },
    "कृष्णा (Krishna / Machilipatnam)": { lat: 16.1875, lon: 81.1389, name: "कृष्णा, आंध्र प्रदेश" },
    "चित्तूर (Chittoor)": { lat: 13.2172, lon: 79.1003, name: "चित्तूर, आंध्र प्रदेश" }
  },
  "तेलंगाना (Telangana)": {
    "हैदराबाद (Hyderabad)": { lat: 17.3850, lon: 78.4867, name: "हैदराबाद, तेलंगाना" },
    "वारंगल (Warangal)": { lat: 17.9689, lon: 79.5941, name: "वारंगल, तेलंगाना" },
    "करीमनगर (Karimnagar)": { lat: 18.4386, lon: 79.1288, name: "करीमनगर, तेलंगाना" },
    "निजामाबाद (Nizamabad)": { lat: 18.6725, lon: 78.0941, name: "निजामाबाद, तेलंगाना" },
    "खम्मम (Khammam)": { lat: 17.2473, lon: 80.1514, name: "खम्मम, तेलंगाना" },
    "नलगोंडा (Nalgonda)": { lat: 17.0575, lon: 79.2684, name: "नलगोंडा, तेलंगाना" },
    "महबूबनगर (Mahabubnagar)": { lat: 16.7488, lon: 77.9856, name: "महबूबनगर, तेलंगाना" }
  },
  "तमिलनाडु (Tamil Nadu)": {
    "चेन्नई (Chennai)": { lat: 13.0827, lon: 80.2707, name: "चेन्नई, तमिलनाडु" },
    "कोयंबटूर (Coimbatore)": { lat: 11.0168, lon: 76.9558, name: "कोयंबटूर, तमिलनाडु" },
    "मदुरै (Madurai)": { lat: 9.9252, lon: 78.1198, name: "मदुरै, तमिलनाडु" },
    "तंजावुर (Thanjavur)": { lat: 10.7870, lon: 79.1378, name: "तंजावुर, तमिलनाडु" },
    "तिरुचिरापल्ली (Tiruchirappalli)": { lat: 10.7905, lon: 78.7047, name: "तिरुचिरापल्ली, तमिलनाडु" },
    "सलेम (Salem)": { lat: 11.6643, lon: 78.1460, name: "सलेम, तमिलनाडु" },
    "इरोड (Erode)": { lat: 11.3410, lon: 77.7172, name: "इरोड, तमिलनाडु" },
    "तिरुनेलवेली (Tirunelveli)": { lat: 8.7139, lon: 77.7567, name: "तिरुनेलवेली, तमिलनाडु" }
  },
  "केरल (Kerala)": {
    "तिरुवनंतपुरम (Thiruvananthapuram)": { lat: 8.5241, lon: 76.9366, name: "तिरुवनंतपुरम, केरल" },
    "कोच्चि (Kochi / Ernakulam)": { lat: 9.9312, lon: 76.2673, name: "कोच्चि, केरल" },
    "पालक्काड (Palakkad)": { lat: 10.7867, lon: 76.6548, name: "पालक्काड, केरल" },
    "वायनाड (Wayanad / Kalpetta)": { lat: 11.6103, lon: 76.0829, name: "वायनाड, केरल" },
    "कोट्टायम (Kottayam)": { lat: 9.5916, lon: 76.5222, name: "कोट्टायम, केरल" },
    "इडुक्की (Idukki / Painavu)": { lat: 9.8500, lon: 76.9700, name: "इडुक्की, केरल" }
  },
  "ओडिशा (Odisha)": {
    "भुवनेश्वर (Bhubaneswar / Khordha)": { lat: 20.2961, lon: 85.8245, name: "भुवनेश्वर, ओडिशा" },
    "कटक (Cuttack)": { lat: 20.4625, lon: 85.8830, name: "कटक, ओडिशा" },
    "संबलपुर (Sambalpur)": { lat: 21.4669, lon: 83.9812, name: "संबलपुर, ओडिशा" },
    "बालासोर (Balasore)": { lat: 21.4934, lon: 86.9135, name: "बालासोर, ओडिशा" },
    "बरगढ़ (Bargarh)": { lat: 21.3333, lon: 83.6167, name: "बरगढ़, ओडिशा" },
    "गंजम (Ganjam / Berhampur)": { lat: 19.3150, lon: 84.7941, name: "गंजम, ओडिशा" }
  },
  "छत्तीसगढ़ (Chhattisgarh)": {
    "रायपुर (Raipur)": { lat: 21.2514, lon: 81.6296, name: "रायपुर, छत्तीसगढ़" },
    "बिलासपुर (Bilaspur)": { lat: 22.0797, lon: 82.1409, name: "बिलासपुर, छत्तीसगढ़" },
    "दुर्ग (Durg)": { lat: 21.1904, lon: 81.2849, name: "दुर्ग, छत्तीसगढ़" },
    "राजनांदगांव (Rajnandgaon)": { lat: 21.0970, lon: 81.0376, name: "राजनांदगांव, छत्तीसगढ़" },
    "धमतरी (Dhamtari)": { lat: 20.7071, lon: 81.5494, name: "धमतरी, छत्तीसगढ़" },
    "जांजगीर-चांपा (Janjgir-Champa)": { lat: 22.0150, lon: 82.5714, name: "जांजगीर-चांपा, छत्तीसगढ़" }
  },
  "झारखंड (Jharkhand)": {
    "रांची (Ranchi)": { lat: 23.3441, lon: 85.3096, name: "रांची, झारखंड" },
    "जमशेदपुर (Jamshedpur / East Singhbhum)": { lat: 22.8046, lon: 86.2029, name: "जमशेदपुर, झारखंड" },
    "धनबाद (Dhanbad)": { lat: 23.7957, lon: 86.4304, name: "धनबाद, झारखंड" },
    "हजारीबाग (Hazaribagh)": { lat: 23.9968, lon: 85.3690, name: "हजारीबाग, झारखंड" },
    "देवघर (Deoghar)": { lat: 24.4826, lon: 86.7001, name: "देवघर, झारखंड" }
  },
  "असम (Assam)": {
    "गुवाहाटी (Guwahati / Kamrup)": { lat: 26.1445, lon: 91.7362, name: "गुवाहाटी, असम" },
    "जोरहाट (Jorhat)": { lat: 26.7509, lon: 94.2037, name: "जोरहाट, असम" },
    "डिब्रूगढ़ (Dibrugarh)": { lat: 27.4728, lon: 94.9120, name: "डिब्रूगढ़, असम" },
    "सिलचर (Silchar / Cachar)": { lat: 24.8333, lon: 92.7789, name: "सिलचर, असम" },
    "नगांव (Nagaon)": { lat: 26.3452, lon: 92.6840, name: "नगांव, असम" }
  },
  "हिमाचल प्रदेश (Himachal Pradesh)": {
    "शिमला (Shimla)": { lat: 31.1048, lon: 77.1734, name: "शिमला, हिमाचल प्रदेश" },
    "कांगड़ा (Kangra / Dharamshala)": { lat: 32.0998, lon: 76.2691, name: "कांगड़ा, हिमाचल प्रदेश" },
    "मंडी (Mandi)": { lat: 31.7087, lon: 76.9320, name: "मंडी, हिमाचल प्रदेश" },
    "कुल्लू (Kullu)": { lat: 31.9579, lon: 77.1095, name: "कुल्लू, हिमाचल प्रदेश" },
    "सोलन (Solan)": { lat: 30.9045, lon: 77.0967, name: "सोलन, हिमाचल प्रदेश" }
  },
  "उत्तराखंड (Uttarakhand)": {
    "देहरादून (Dehradun)": { lat: 30.3165, lon: 78.0322, name: "देहरादून, उत्तराखंड" },
    "हरिद्वार (Haridwar)": { lat: 29.9457, lon: 78.1642, name: "हरिद्वार, उत्तराखंड" },
    "उधम सिंह नगर (Udham Singh Nagar / Rudrapur)": { lat: 28.9800, lon: 79.4000, name: "उधम सिंह नगर, उत्तराखंड" },
    "नैनीताल (Nainital)": { lat: 29.3919, lon: 79.4542, name: "नैनीताल, उत्तराखंड" }
  },
  "गोवा (Goa)": {
    "उत्तर गोवा (North Goa / Panaji)": { lat: 15.4909, lon: 73.8278, name: "उत्तर गोवा, गोवा" },
    "दक्षिण गोवा (South Goa / Margao)": { lat: 15.2832, lon: 73.9862, name: "दक्षिण गोवा, गोवा" }
  },
  "त्रिपुरा (Tripura)": {
    "अगरतला (Agartala / West Tripura)": { lat: 23.8315, lon: 91.2868, name: "अगरतला, त्रिपुरा" },
    "गोमती (Gomati / Udaipur)": { lat: 23.5333, lon: 91.4833, name: "गोमती, त्रिपुरा" }
  },
  "मेघालय (Meghalaya)": {
    "शिलांग (Shillong / East Khasi Hills)": { lat: 25.5788, lon: 91.8933, name: "शिलांग, मेघालय" },
    "तुरा (Tura / West Garo Hills)": { lat: 25.5144, lon: 90.2032, name: "तुरा, मेघालय" }
  },
  "मणिपुर (Manipur)": {
    "इम्फाल (Imphal / Imphal West)": { lat: 24.8170, lon: 93.9368, name: "इम्फाल, मणिपुर" },
    "बिष्णुपुर (Bishnupur)": { lat: 24.6333, lon: 93.7667, name: "बिष्णुपुर, मणिपुर" }
  },
  "नागालैंड (Nagaland)": {
    "कोहिमा (Kohima)": { lat: 25.6751, lon: 94.1086, name: "कोहिमा, नागालैंड" },
    "दीमापुर (Dimapur)": { lat: 25.9068, lon: 93.7271, name: "दीमापुर, नागालैंड" }
  },
  "मिज़ोरम (Mizoram)": {
    "आइज़ोल (Aizawl)": { lat: 23.7271, lon: 92.7176, name: "आइज़ोल, मिज़ोरम" },
    "लुंगलेई (Lunglei)": { lat: 22.8671, lon: 92.7656, name: "लुंगलेई, मिज़ोरम" }
  },
  "अरुणाचल प्रदेश (Arunachal Pradesh)": {
    "ईटानगर (Itanagar / Papum Pare)": { lat: 27.0844, lon: 93.6053, name: "ईटानगर, अरुणाचल प्रदेश" },
    "पासीघाट (Pasighat / East Siang)": { lat: 28.0667, lon: 95.3333, name: "पासीघाट, अरुणाचल प्रदेश" }
  },
  "सिक्किम (Sikkim)": {
    "गंगटोक (Gangtok / East Sikkim)": { lat: 27.3389, lon: 88.6065, name: "गंगटोक, सिक्किम" },
    "नामची (Namchi / South Sikkim)": { lat: 27.1667, lon: 88.3500, name: "नामची, सिक्किम" }
  },

  // ----------------- 8 UNION TERRITORIES -----------------
  "दिल्ली (Delhi)": {
    "नई दिल्ली (New Delhi)": { lat: 28.6139, lon: 77.2090, name: "नई दिल्ली, दिल्ली" },
    "उत्तर पश्चिम दिल्ली (North West Delhi / Kanjhawala)": { lat: 28.7282, lon: 77.0135, name: "उत्तर पश्चिम दिल्ली, दिल्ली" },
    "दक्षिण पश्चिम दिल्ली (South West Delhi / Najafgarh)": { lat: 28.6128, lon: 76.9855, name: "दक्षिण पश्चिम दिल्ली, दिल्ली" },
    "उत्तर दिल्ली (North Delhi / Alipur)": { lat: 28.8020, lon: 77.1328, name: "उत्तर दिल्ली, दिल्ली" }
  },
  "जम्मू और कश्मीर (Jammu and Kashmir)": {
    "जम्मू (Jammu)": { lat: 32.7266, lon: 74.8570, name: "जम्मू, जम्मू और कश्मीर" },
    "श्रीनगर (Srinagar)": { lat: 34.0837, lon: 74.7973, name: "श्रीनगर, जम्मू और कश्मीर" },
    "अनंतनाग (Anantnag)": { lat: 33.7311, lon: 75.1522, name: "अनंतनाग, जम्मू और कश्मीर" },
    "बारामूला (Baramulla)": { lat: 34.1980, lon: 74.3636, name: "बारामूला, जम्मू और कश्मीर" },
    "कठुआ (Kathua)": { lat: 32.3872, lon: 75.5244, name: "कठुआ, जम्मू और कश्मीर" }
  },
  "लद्दाख (Ladakh)": {
    "लेह (Leh)": { lat: 34.1526, lon: 77.5771, name: "लेह, लद्दाख" },
    "कारगिल (Kargil)": { lat: 34.5539, lon: 76.1349, name: "कारगिल, लद्दाख" }
  },
  "चंडीगढ़ (Chandigarh)": {
    "चंडीगढ़ (Chandigarh)": { lat: 30.7333, lon: 76.7794, name: "चंडीगढ़" }
  },
  "पुदुचेरी (Puducherry)": {
    "पुदुचेरी (Puducherry)": { lat: 11.9416, lon: 79.8083, name: "पुदुचेरी" },
    "कराइकाल (Karaikal)": { lat: 10.9254, lon: 79.8380, name: "कराइकाल, पुदुचेरी" }
  },
  "दादरा और नगर हवेली एवं दमन और दीव (Dadra & Nagar Haveli & Daman & Diu)": {
    "दमन (Daman)": { lat: 20.3974, lon: 72.8328, name: "दमन" },
    "सिलवासा (Silvassa)": { lat: 20.2763, lon: 73.0083, name: "सिलवासा" }
  },
  "अंडमान और निकोबार (Andaman & Nicobar Islands)": {
    "पोर्ट ब्लेयर (Port Blair)": { lat: 11.6234, lon: 92.7265, name: "पोर्ट ब्लेयर, अंडमान और निकोबार" }
  },
  "लक्षद्वीप (Lakshadweep)": {
    "कवरत्ती (Kavaratti)": { lat: 10.5667, lon: 72.6417, name: "कवरत्ती, लक्षद्वीप" }
  }
};

/**
 * Normalizes state name to match an INDIA_LOCATIONS key.
 * Handles English name, Hindi name, or combined bilingual string.
 */
function resolveStateKey(stateQuery) {
  if (!stateQuery) return null;
  const q = stateQuery.trim().toLowerCase();
  
  // Exact or contains match in key
  for (const key of Object.keys(INDIA_LOCATIONS)) {
    if (key.toLowerCase() === q) return key;
    if (key.toLowerCase().includes(q) || q.includes(key.toLowerCase())) return key;
  }
  
  // Check English part inside parentheses
  for (const key of Object.keys(INDIA_LOCATIONS)) {
    const m = key.match(/\(([^)]+)\)/);
    if (m && (m[1].toLowerCase() === q || m[1].toLowerCase().includes(q) || q.includes(m[1].toLowerCase()))) {
      return key;
    }
  }

  return Object.keys(INDIA_LOCATIONS)[0];
}

/**
 * Returns a list of district names for the given state.
 */
function getDistrictsForState(stateName) {
  const resolved = resolveStateKey(stateName);
  if (!resolved || !INDIA_LOCATIONS[resolved]) return [];
  return Object.keys(INDIA_LOCATIONS[resolved]);
}

/**
 * Initializes cascading State and District selects.
 * @param {string} stateSelectId - The ID of the state <select>
 * @param {string} districtSelectId - The ID of the district <select>
 * @param {Object} [options]
 * @param {Function} [options.onSelect] - Callback triggered when district is selected
 * @param {Function} [options.onStateChange] - Callback triggered when state changes
 * @param {string} [options.defaultState] - Optional default state name
 * @param {string} [options.defaultDistrict] - Optional default district name
 */
function setupCascadingStateDistrict(stateSelectId, districtSelectId, options = {}) {
  const stateEl = document.getElementById(stateSelectId);
  const distEl = document.getElementById(districtSelectId);
  if (!stateEl || !distEl) return;

  // 1. Populate States cleanly
  stateEl.innerHTML = '<option value="">-- राज्य चुनें (Select State) --</option>';
  const sortedStates = Object.keys(INDIA_LOCATIONS);
  sortedStates.forEach(state => {
    const opt = document.createElement("option");
    opt.value = state;
    opt.textContent = state;
    stateEl.appendChild(opt);
  });

  // 2. On State Change -> Populate Districts
  stateEl.addEventListener("change", () => {
    const rawState = stateEl.value;
    const resolvedState = resolveStateKey(rawState);
    distEl.innerHTML = '<option value="">-- जिला चुनें (Select District) --</option>';

    if (resolvedState && INDIA_LOCATIONS[resolvedState]) {
      distEl.disabled = false;
      const dists = INDIA_LOCATIONS[resolvedState];
      Object.keys(dists).forEach(district => {
        const opt = document.createElement("option");
        opt.value = district;
        opt.textContent = district;
        distEl.appendChild(opt);
      });
    } else {
      distEl.disabled = true;
    }

    if (options.onStateChange) {
      options.onStateChange(resolvedState || rawState);
    }
  });

  // 3. On District Change -> Trigger Callback
  distEl.addEventListener("change", () => {
    const rawState = stateEl.value;
    const resolvedState = resolveStateKey(rawState);
    const selectedDist = distEl.value;
    if (resolvedState && selectedDist && INDIA_LOCATIONS[resolvedState][selectedDist]) {
      const info = INDIA_LOCATIONS[resolvedState][selectedDist];
      if (options.onSelect) {
        options.onSelect({
          state: resolvedState,
          district: selectedDist,
          lat: info.lat,
          lon: info.lon,
          name: info.name
        });
      }
    }
  });

  // Set defaults if provided
  const targetState = resolveStateKey(options.defaultState) || sortedStates[0];
  if (targetState && INDIA_LOCATIONS[targetState]) {
    stateEl.value = targetState;
    distEl.innerHTML = '<option value="">-- जिला चुनें (Select District) --</option>';
    distEl.disabled = false;
    const dists = INDIA_LOCATIONS[targetState];
    Object.keys(dists).forEach(district => {
      const opt = document.createElement("option");
      opt.value = district;
      opt.textContent = district;
      distEl.appendChild(opt);
    });

    if (options.defaultDistrict) {
      const dMatch = Object.keys(dists).find(d => 
        d.toLowerCase() === options.defaultDistrict.toLowerCase() ||
        d.toLowerCase().includes(options.defaultDistrict.toLowerCase())
      );
      if (dMatch) {
        distEl.value = dMatch;
      }
    }
  }
}

// Global Exports
if (typeof window !== "undefined") {
  window.INDIA_LOCATIONS = INDIA_LOCATIONS;
  window.AGRI_LOCATIONS = INDIA_LOCATIONS; // Backward compatibility
  window.resolveStateKey = resolveStateKey;
  window.getDistrictsForState = getDistrictsForState;
  window.setupCascadingStateDistrict = setupCascadingStateDistrict;
}
