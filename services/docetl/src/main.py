
#!/usr/bin/env python3
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "DocETL", "port": 5001})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "DocETL",
        "status": "running",
        "endpoints": ["/health", "/process"],
        "description": "Document ETL Processing Service"
    })

@app.route('/process', methods=['POST'])
def process_document():
    return jsonify({
        "status": "success",
        "message": "Document ETL processing would happen here",
        "processed": True
    })

if __name__ == '__main__':
    print("📄 Starting DocETL Service on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)
