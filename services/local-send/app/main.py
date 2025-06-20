
#!/usr/bin/env python3
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "LocalSend", "port": 5050})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "LocalSend",
        "status": "running",
        "endpoints": ["/health", "/send", "/receive"],
        "description": "Local File Transfer Service"
    })

@app.route('/send', methods=['POST'])
def send_file():
    return jsonify({
        "status": "success",
        "message": "File would be sent here",
        "transfer_id": "tx_123456"
    })

@app.route('/receive', methods=['GET'])
def receive_file():
    return jsonify({
        "status": "success",
        "available_files": [],
        "total_files": 0
    })

if __name__ == '__main__':
    print("📤 Starting LocalSend Service on port 5050...")
    app.run(host='0.0.0.0', port=5050, debug=False)
