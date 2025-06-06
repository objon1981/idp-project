import pytesseract
import easyocr
import cv2
from PIL import Image
import numpy as np
import io

# EasyOCR model
reader = easyocr.Reader(['en'])

def extract_text_easyocr(image_bytes):
    image = np.array(Image.open(io.BytesIO(image_bytes)))
    result = reader.readtext(image, detail=0)
    return "\n".join(result)

def extract_text_tesseract(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)
