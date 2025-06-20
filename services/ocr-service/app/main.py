
#!/usr/bin/env python3
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "OCR Service", "port": 8080})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "OCR Service",
        "status": "running",
        "endpoints": ["/health", "/ocr"],
        "description": "Optical Character Recognition Service"
    })

@app.route('/ocr', methods=['POST'])
def ocr_process():
    return jsonify({
        "status": "success",
        "message": "OCR processing would happen here",
        "extracted_text": "Sample extracted text from document"
    })

if __name__ == '__main__':
    print("🔍 Starting OCR Service on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)
