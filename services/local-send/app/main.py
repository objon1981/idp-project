from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from utils import save_file, generate_secure_key

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/send', methods=['POST'])
def send():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    filename = save_file(file, UPLOAD_FOLDER)
    key = generate_secure_key(filename)
    
    return jsonify({'message': 'File received', 'file': filename, 'key': key})

@app.route('/receive/<key>', methods=['GET'])
def receive(key):
    filepath = os.path.join(UPLOAD_FOLDER, key)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
