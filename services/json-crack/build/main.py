
#!/usr/bin/env python3
from flask import Flask, jsonify, request
import json

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "JSON Crack", "port": 3000})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "JSON Crack",
        "status": "running",
        "endpoints": ["/health", "/visualize", "/validate"],
        "description": "JSON Visualization and Analysis Service"
    })

@app.route('/visualize', methods=['POST'])
def visualize_json():
    return jsonify({
        "status": "success",
        "message": "JSON visualization would happen here",
        "visualization_url": "/viz/sample"
    })

@app.route('/validate', methods=['POST'])
def validate_json():
    try:
        data = request.get_json()
        return jsonify({
            "status": "success",
            "valid": True,
            "message": "JSON is valid"
        })
    except:
        return jsonify({
            "status": "error",
            "valid": False,
            "message": "Invalid JSON"
        }), 400

if __name__ == '__main__':
    print("🔧 Starting JSON Crack Service on port 3000...")
    app.run(host='0.0.0.0', port=3000, debug=False)
