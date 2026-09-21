import re

LANGUAGE_MAP = {
    "hi": "Hindi",
    "en": "English",
    "bn": "Bengali",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "pa": "Punjabi"
}

def detect_language(text: str) -> str:
    if not text:
        return "en"
    
    # Devanagari range (Hindi, Marathi)
    if re.search(r'[ऀ-ॿ]', text):
        # Specific Marathi words check
        if any(w in text for w in ['आहे', 'नाही', 'कसे', 'शेतकरी']):
            return "mr"
        return "hi"
    # Bengali / Assamese
    if re.search(r'[ঀ-৿]', text):
        return "bn"
    # Tamil
    if re.search(r'[஀-௿]', text):
        return "ta"
    # Telugu
    if re.search(r'[ఀ-౿]', text):
        return "te"
    # Kannada
    if re.search(r'[ಀ-೿]', text):
        return "kn"
    # Gujarati
    if re.search(r'[઀-૿]', text):
        return "gu"
    # Gurmukhi (Punjabi)
    if re.search(r'[਀-੿]', text):
        return "pa"
        
    return "en"
