"""
PlantVillage ICAR Agronomic Diagnostic Knowledge Base & Offline Classifier
Mapped from Kaggle Dataset: snikhilrao/crop-disease-detection-dataset
"""

PLANT_VILLAGE_DISEASE_DB = {
    "Tomato - Early Blight": {
        "crop_hi": "टमाटर (Tomato)",
        "disease_hi": "अगेती झुलसा (Early Blight)",
        "pathogen": "Alternaria solani (फफूंद)",
        "symptoms": "निचली पत्तियों पर गहरे भूरे रंग के छल्लेदार धब्बे (Target spots) बनना, पत्तियों का पीला पड़कर सूखना।",
        "organic_treatment": "नीम तेल 5ml/लीटर + ट्राइकोडर्मा विरिडी (Trichoderma viride) 5 ग्राम/लीटर का पर्णीय छिड़काव करें।",
        "chemical_treatment": "कॉपर ऑक्सीक्लोराइड 50% WP @ 2.5 ग्राम/लीटर अथवा मैंकोजेब 75% WP @ 2 ग्राम/लीटर पानी में घोलकर छिड़कें।",
        "prevention": "फसल चक्र अपनाएं, पौधों के बीच पर्याप्त दूरी रखें तथा संक्रमित पत्तियों को तोड़कर नष्ट करें।"
    },
    "Tomato - Late Blight": {
        "crop_hi": "टमाटर (Tomato)",
        "disease_hi": "पछेती झुलसा (Late Blight)",
        "pathogen": "Phytophthora infestans",
        "symptoms": "पत्तियों के किनारों पर जलभराव जैसे भूरे-काले धब्बे और पत्तियों के नीचे सफेद फफूंद दिखना।",
        "organic_treatment": "बोर्डो मिश्रण 1% (Bordeaux Mixture) का छिड़काव करें। खेत में अधिक नमी जमा न होने दें।",
        "chemical_treatment": "सिमोक्सानिल 8% + मैंकोजेब 64% WP @ 2.5 ग्राम/लीटर अथवा मेंडिप्रोपामिड @ 1ml/लीटर का तुरंत छिड़काव करें।",
        "prevention": "संक्रमित पौधों को तुरंत उखाड़ें और हवा का संचार सुगम रखें।"
    },
    "Tomato - Yellow Leaf Curl Virus": {
        "crop_hi": "टमाटर (Tomato)",
        "disease_hi": "पत्ती मरोड़ रोग (Leaf Curl Virus)",
        "pathogen": "Tomato Leaf Curl Begomovirus (सफेद मक्खी द्वारा प्रसारित)",
        "symptoms": "पत्तियां ऊपर की ओर मुड़ना, छोटी व मोटी हो जाना, पौधे का बौना रह जाना और फल न लगना।",
        "organic_treatment": "पीले चिपचिपे कार्ड (Yellow Sticky Traps) 15-20 प्रति एकड़ लगाएं। नीम तेल 10,000 PPM @ 3ml/लीटर छिड़कें।",
        "chemical_treatment": "सफेद मक्खी नियंत्रण हेतु इमिडाक्लोप्रिड 17.8% SL @ 0.5ml/लीटर अथवा एसिटामिप्रिड 20% SP @ 0.3g/लीटर का छिड़काव करें।",
        "prevention": "नर्सरी को नेट हाउस में तैयार करें तथा रोगग्रस्त पौधों को खेत से उखाड़कर नष्ट करें।"
    },
    "Tomato - Bacterial Spot": {
        "crop_hi": "टमाटर (Tomato)",
        "disease_hi": "जीवाणु धब्बा रोग (Bacterial Spot)",
        "pathogen": "Xanthomonas campestris",
        "symptoms": "पत्तियों पर छोटे, काले-भूरे तैलीय धब्बे जिनके चारों ओर पीला छल्ला होता है।",
        "organic_treatment": "स्यूडोमोनास फ्लोरेसेंस (Pseudomonas fluorescens) 5g/लीटर का छिड़काव करें।",
        "chemical_treatment": "स्ट्रेप्टोसाइक्लिन 1 ग्राम + कॉपर ऑक्सीक्लोराइड 30 ग्राम प्रति 15 लीटर पानी के पंप में मिलाकर छिड़कें।",
        "prevention": "बीजोपचार करें एवं खेत में जल निकासी की उचित व्यवस्था रखें।"
    },
    "Tomato - Septoria Leaf Spot": {
        "crop_hi": "टमाटर (Tomato)",
        "disease_hi": "सेप्टोरिया पत्ती धब्बा (Septoria Leaf Spot)",
        "pathogen": "Septoria lycopersici",
        "symptoms": "पत्तियों पर छोटे गोलाकार धब्बे जिनका केंद्र भूरा-सफेद और किनारा गहरा काला होता है।",
        "organic_treatment": "जैविक फफूंदनाशक ट्राइकोडर्मा हरजिएनम 5g/लीटर का छिड़काव।",
        "chemical_treatment": "क्लोरोथैलोनिल 75% WP @ 2g/लीटर या टेबुकोनाजोल @ 1ml/लीटर पानी में छिड़कें।",
        "prevention": "पौधों पर नीचे से पानी की छींटें न पड़ने दें (मल्चिंग का उपयोग करें)।"
    },
    "Potato - Early Blight": {
        "crop_hi": "आलू (Potato)",
        "disease_hi": "अगेती झुलसा (Early Blight)",
        "pathogen": "Alternaria solani",
        "symptoms": "पत्तियों पर संकेंद्रित छल्लों वाले भूरे धब्बे, पत्तियां झुलसकर गिरना।",
        "organic_treatment": "खट्टी छाछ (Buttermilk) 50ml + हींग 2g प्रति लीटर पानी का छिड़काव।",
        "chemical_treatment": "मैंकोजेब 75% WP @ 2.5 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "prevention": "रोग-मुक्त प्रमाणित बीज कंद बोएं।"
    },
    "Potato - Late Blight": {
        "crop_hi": "आलू (Potato)",
        "disease_hi": "पछेती झुलसा (Late Blight)",
        "pathogen": "Phytophthora infestans",
        "symptoms": "पत्तियों पर गीले काले-भूरे धब्बे, ठंडे और कोहरे वाले मौसम में तेजी से पूरे खेत में फैलना।",
        "organic_treatment": "तांबा युक्त बोर्डो मिश्रण 1% का अग्रिम छिड़काव।",
        "chemical_treatment": "मेटालेक्सिल 8% + मैंकोजेब 64% WP (रिडोमिल) @ 2.5 ग्राम/लीटर का तत्काल छिड़काव करें।",
        "prevention": "मौसम विभाग के झुलसा अलर्ट पर नजर रखें और कंदों को मिट्टी से अच्छी तरह ढकें।"
    },
    "Corn (Maize) - Common Rust": {
        "crop_hi": "मक्का (Corn / Maize)",
        "disease_hi": "सामान्य गेरुआ रोग (Common Rust)",
        "pathogen": "Puccinia sorghi",
        "symptoms": "पत्तियों के दोनों ओर भूरे-लाल रंग के उभरे हुए फफोले (Pustules) बनना, जो छूने पर पाउडर छोड़ते हैं।",
        "organic_treatment": "नीम का काढ़ा अथवा नीम तेल 5ml/L का छिड़काव करें।",
        "chemical_treatment": "एजोक्सीस्ट्रोबिन 18.2% + डिफेनोकोनाजोल 11.4% SC (अमीस्टार टॉप) @ 1ml/लीटर का छिड़काव करें।",
        "prevention": "प्रतिरोधी किस्में लगाएं तथा पोटाश खाद की संतुलित मात्रा दें।"
    },
    "Corn (Maize) - Northern Leaf Blight": {
        "crop_hi": "मक्का (Corn / Maize)",
        "disease_hi": "उत्तरी पत्ती झुलसा (Northern Leaf Blight)",
        "pathogen": "Exserohilum turcicum",
        "symptoms": "पत्तियों पर लंबे, नाव के आकार के धूसर-भूरे धब्बे (Cigar-shaped lesions)।",
        "organic_treatment": "स्यूडोमोनास फ्लोरेसेंस 10 ग्राम/लीटर का पर्णीय छिड़काव।",
        "chemical_treatment": "प्रोपिकोनाजोल 25% EC (टिल्ट) @ 1ml/लीटर पानी में मिलाकर छिड़कें।",
        "prevention": "फसल अवशेषों को गहरा जोतकर नष्ट करें।"
    },
    "Bell Pepper - Bacterial Spot": {
        "crop_hi": "शिमला मिर्च / मिर्च (Bell Pepper / Chilli)",
        "disease_hi": "जीवाणु पत्ती धब्बा (Bacterial Spot)",
        "pathogen": "Xanthomonas euvesicatoria",
        "symptoms": "पत्तियों और फलों पर खुरदुरे, उभरे हुए गहरे भूरे धब्बे, पत्तियों का झड़ना।",
        "organic_treatment": "तांबा सल्फेट + चूना (बोर्डो मिश्रण 0.5%) या नीम अर्क का प्रयोग।",
        "chemical_treatment": "कॉपर हाइड्राक्साइड 53.8% DF @ 2 ग्राम/लीटर पानी का छिड़काव।",
        "prevention": "गर्म पानी से बीजोपचार (50°C पर 25 मिनट) करें।"
    },
    "Apple - Apple Scab": {
        "crop_hi": "सेब (Apple)",
        "disease_hi": "सेब स्केब रोग (Apple Scab)",
        "pathogen": "Venturia inaequalis",
        "symptoms": "पत्तियों व फलों पर जैतून-हरे से काले मखमली धब्बे, फलों का फटना।",
        "organic_treatment": "सल्फर 80% WDG @ 3 ग्राम/लीटर का कलियों के फूटने के समय छिड़काव।",
        "chemical_treatment": "डोडिन 65% WP @ 0.75 ग्राम/लीटर अथवा कैप्टान 50% WP @ 2.5 ग्राम/लीटर का छिड़काव।",
        "prevention": "पतझड़ में गिरी पत्तियों पर 5% यूरिया का छिड़काव कर अपघटन तेज करें।"
    }
}

def lookup_plant_village_advisory(label: str) -> dict:
    """Returns scientific diagnostic advisory for PlantVillage classes."""
    for key, data in PLANT_VILLAGE_DISEASE_DB.items():
        if key.lower() in label.lower() or label.lower() in key.lower():
            return data
    return None
