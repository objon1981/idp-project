from flask import Flask, request, jsonify
import os
import logging
from ocr_engine import OCREngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize OCR Engine
try:
    ocr_engine = OCREngine(languages=['en'], gpu=False)  # Set gpu=True if you have CUDA
    logger.info("OCR Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OCR Engine: {str(e)}")
    ocr_engine = None

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'service': 'EasyOCR Microservice',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'upload': '/ocr/upload',
            'base64': '/ocr/base64',
            'batch': '/ocr/batch'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if ocr_engine else 'unhealthy',
        'service': 'EasyOCR Microservice',
        'version': '1.0.0',
        'dependencies': {
            'easyocr': '1.7.2',
            'flask': '3.1.1',
            'pillow': '10.4.0',
            'torch': '2.7.0'
        }
    })

@app.route('/ocr/upload', methods=['POST'])
def ocr_upload():
    """OCR endpoint for file upload"""
    if not ocr_engine:
        return jsonify({'error': 'OCR engine not initialized'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Process with OCR engine
        results = ocr_engine.process_image_upload(file)
        
        return jsonify({
            'success': True,
            **results
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in OCR upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/ocr/base64', methods=['POST'])
def ocr_base64():
    """OCR endpoint for base64 encoded images"""
    if not ocr_engine:
        return jsonify({'error': 'OCR engine not initialized'}), 500
    
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Process with OCR engine
        results = ocr_engine.process_image_base64(data['image'])
        
        return jsonify({
            'success': True,
            **results
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in OCR base64: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/ocr/batch', methods=['POST'])
def ocr_batch():
    """Batch OCR processing"""
    if not ocr_engine:
        return jsonify({'error': 'OCR engine not initialized'}), 500
    
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files selected'}), 400
        
        results = ocr_engine.process_batch(files)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_files': len(files),
            'processed_files': len([r for r in results if r.get('success', False)])
        })
        
    except Exception as e:
        logger.error(f"Error in batch OCR: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large (max 16MB)'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting EasyOCR microservice on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)