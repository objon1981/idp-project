
#!/usr/bin/env python3
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Pake", "port": 8081})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "Pake",
        "status": "running",
        "endpoints": ["/health", "/package", "/build"],
        "description": "Web App Packaging Service"
    })

@app.route('/package', methods=['POST'])
def package_app():
    return jsonify({
        "status": "success",
        "message": "App packaging would happen here",
        "package_id": "pkg_123456"
    })

@app.route('/build', methods=['POST'])
def build_app():
    return jsonify({
        "status": "success",
        "message": "App build would happen here",
        "build_id": "build_123456"
    })

if __name__ == '__main__':
    print("📦 Starting Pake Service on port 8081...")
    app.run(host='0.0.0.0', port=8081, debug=False)
