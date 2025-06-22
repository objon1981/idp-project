#!/usr/bin/env python3
from flask import Flask, jsonify, request # type: ignore
import os
import uuid
from etl import extract_data, save_output  # ✅ Import from etl.py

app = Flask(__name__)

# ✅ /health endpoint for monitoring
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "DocETL",
        "port": 5002
    })

# 🏠 Root info
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "DocETL",
        "status": "running",
        "endpoints": ["/health", "/process"],
        "description": "Document ETL Processing Service"
    })

# ✅ Actual document processing logic
@app.route('/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    filename = file.filename
    temp_input_path = f"/tmp/{uuid.uuid4().hex}_{filename}"
    file.save(temp_input_path)

    try:
        extracted_text = extract_data(temp_input_path)
        output_path = f"/tmp/output_{uuid.uuid4().hex}.txt"
        save_output(output_path, extracted_text)

        return jsonify({
            "status": "success",
            "filename": filename,
            "output_path": output_path,
            "preview": extracted_text[:500],  # Send a preview of the extracted text
            "timestamp": uuid.uuid1().ctime()  # Optional: readable time
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("📄 Starting DocETL Service on port 5001...")
    app.run(host='0.0.0.0', port=5002, debug=False)
