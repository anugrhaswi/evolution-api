from flask import Flask, request, jsonify
import cv2
import numpy as np
import easyocr
import re
import base64

app = Flask(__name__)
# Initialize EasyOCR globally
reader = easyocr.Reader(['en'], gpu=False)

def extract(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray, detail=1)
    full_text = " ".join([r[1] for r in results])

    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    dob_pattern = r'(?:DOB|Date of Birth|Year of Birth)[:\s]*(\d{2}/\d{2}/\d{4}|\d{4})'
    gender_pattern = r'\b(Male|Female|MALE|FEMALE|TRANSGENDER)\b'
    name_pattern = r'Government of India[^A-Za-z]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    father_pattern = r'Father[\:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'

    aadhaar_num = re.search(aadhaar_pattern, full_text)
    dob = re.search(dob_pattern, full_text, re.IGNORECASE)
    gender = re.search(gender_pattern, full_text, re.IGNORECASE)
    name = re.search(name_pattern, full_text)
    father = re.search(father_pattern, full_text, re.IGNORECASE)

    aadhaar_label_idx = None
    for i, (bbox, text, _) in enumerate(results):
        if re.search(r'Aadhaar No', text):
            aadhaar_label_idx = i
            break
    card_type = "long" if aadhaar_label_idx is not None else "short"

    address = "Not Applicable"
    if aadhaar_label_idx is not None and aadhaar_label_idx > 4:
        addr_texts = []
        for i in range(4, aadhaar_label_idx):
            text = results[i][1].strip()
            normalized = text.translate(str.maketrans('०१२३४५६७८९', '0123456789'))
            if not normalized.isascii():
                continue
            if re.search(r'[A-Z]{2}\d{6,}', normalized):
                continue
            addr_texts.append(normalized)
        address = ", ".join(addr_texts) if addr_texts else "Not Found"

    aadhaar_number = aadhaar_num.group(0).replace(' ', '') if aadhaar_num else None

    return jsonify({
        "status": "success",
        "card_type": card_type,
        "aadhaar_found": aadhaar_number is not None,
        "data": {
            "aadhaar_number": aadhaar_number,
            "name": name.group(1) if name else "Not Found",
            "father_name": father.group(1) if father else "Not Found",
            "dob": dob.group(1) if dob else "Not Found",
            "gender": gender.group(0).upper() if gender else "Not Found",
            "address": address
        }
    })

@app.route('/ocr', methods=['POST'])
def process_aadhaar():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return extract(img)

@app.route('/ocr/base64', methods=['POST'])
def process_aadhaar_base64():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({"error": "No image provided"}), 400
    image_bytes = base64.b64decode(data['image'])
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    return extract(img)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)