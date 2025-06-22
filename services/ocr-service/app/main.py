import os
import tempfile
import traceback
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from logging.handlers import RotatingFileHandler
from prometheus_client import Counter, Histogram, generate_latest
from ocr_engine import extract_text_easyocr, extract_text_tesseract

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Metrics
OCR_REQUESTS = Counter('ocr_requests_total', 'Total OCR requests', ['engine', 'status'])
OCR_PROCESSING_TIME = Histogram('ocr_processing_seconds', 'Time spent processing OCR', ['engine'])

# Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler('logs/ocr.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('OCR Service startup')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, "Valid"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'ocr-service',
        'version': '1.0.0'
    }), 200

@app.route('/metrics')
def metrics():
    return generate_latest()

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        OCR_REQUESTS.labels(engine='unknown', status='error').inc()
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    engine = request.args.get('engine', 'tesseract').lower()
    
    if engine not in ['tesseract', 'easyocr']:
        OCR_REQUESTS.labels(engine=engine, status='error').inc()
        return jsonify({"error": "Invalid engine. Use 'tesseract' or 'easyocr'"}), 400

    # Validate file
    is_valid, message = validate_file(file)
    if not is_valid:
        OCR_REQUESTS.labels(engine=engine, status='error').inc()
        return jsonify({"error": message}), 400

    try:
        # Read file content
        image_bytes = file.read()
        
        if not image_bytes:
            OCR_REQUESTS.labels(engine=engine, status='error').inc()
            return jsonify({"error": "Failed to read file content"}), 400

        # Process with selected engine
        with OCR_PROCESSING_TIME.labels(engine=engine).time():
            if engine == 'easyocr':
                text = extract_text_easyocr(image_bytes)
            else:
                text = extract_text_tesseract(image_bytes)

        OCR_REQUESTS.labels(engine=engine, status='success').inc()
        
        response = {
            "engine": engine,
            "text": text,
            "filename": secure_filename(file.filename),
            "text_length": len(text)
        }
        
        app.logger.info(f"Successfully processed file with {engine}: {len(text)} characters extracted")
        return jsonify(response)

    except Exception as e:
        OCR_REQUESTS.labels(engine=engine, status='error').inc()
        app.logger.error(f"OCR processing failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "OCR processing failed",
            "details": str(e) if app.debug else "Internal server error"
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"}), 413

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    setup_logging()
    app.run(host='0.0.0.0', port=5001, debug=False)