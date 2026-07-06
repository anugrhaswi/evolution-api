import cv2
import easyocr
import re
import os

def test_local_aadhaar(image_path):
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file '{image_path}' not found!")
        return

    print("⏳ Initializing OCR Engine (this takes a moment on first run)...")
    reader = easyocr.Reader(['en', 'hi'], gpu=False)
    
    print(f"📸 Reading image: {image_path}")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    print("🔍 Running text extraction...")
    results = reader.readtext(gray, detail=0)
    full_text = " ".join(results)
    
    print("\n--- 📝 Raw Text Extracted ---")
    print(full_text)
    print("-----------------------------\n")
    
    # Matching regex patterns
    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    dob_pattern = r'(?:DOB|Date of Birth|Year of Birth)[:\s]*(\d{2}/\d{2}/\d{4}|\d{4})'
    gender_pattern = r'\b(Male|Female|MALE|FEMALE|TRANSGENDER)\b'
    
    aadhaar_num = re.search(aadhaar_pattern, full_text)
    dob = re.search(dob_pattern, full_text, re.IGNORECASE)
    gender = re.search(gender_pattern, full_text, re.IGNORECASE)
    
    # Masking logic
    raw_aadhaar = aadhaar_num.group(0) if aadhaar_num else None
    masked_aadhaar = f"XXXX XXXX {raw_aadhaar.replace(' ', '')[-4:]}" if raw_aadhaar else "Not Found"
        
    print("--- 🧠 Parsed JSON Result ---")
    print({
        "status": "success",
        "aadhaar_found": True if raw_aadhaar else False,
        "data": {
            "masked_aadhaar_number": masked_aadhaar,
            "dob": dob.group(1) if dob else "Not Found",
            "gender": gender.group(0).upper() if gender else "Not Found"
        }
    })

# ⚡ CHANGE THIS to the path of your sample Aadhaar image file
test_image = "s.jpg" 
test_local_aadhaar(test_image)
