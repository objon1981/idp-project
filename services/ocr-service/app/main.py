from flask import Flask, request, jsonify
from ocr_engine import extract_text_easyocr, extract_text_tesseract

app = Flask(__name__)

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    image_bytes = file.read()
    engine = request.args.get('engine', 'tesseract')

    if engine == 'easyocr':
        text = extract_text_easyocr(image_bytes)
    else:
        text = extract_text_tesseract(image_bytes)

    return jsonify({"engine": engine, "text": text})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
