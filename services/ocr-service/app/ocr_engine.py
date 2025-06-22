import easyocr # type: ignore
import numpy as np # type: ignore
from PIL import Image
import io
import base64
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class OCREngine:
    def __init__(self, languages: List[str] = ['en'], gpu: bool = False):
        """
        Initialize OCR Engine with EasyOCR
        
        Args:
            languages: List of language codes (e.g., ['en', 'es', 'fr'])
            gpu: Whether to use GPU acceleration
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        
        try:
            logger.info(f"Initializing EasyOCR with languages: {languages}, GPU: {gpu}")
            self.reader = easyocr.Reader(languages, gpu=gpu)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {str(e)}")
            raise

    def process_image_upload(self, file) -> Dict[str, Any]:
        """
        Process uploaded file
        
        Args:
            file: Flask file object
            
        Returns:
            Dictionary with OCR results
        """
        try:
            # Validate file
            if not self._is_valid_image_file(file.filename):
                raise ValueError(f'Invalid file type. Supported: png, jpg, jpeg, gif, bmp, tiff')
            
            # Read file bytes
            image_bytes = file.read()
            
            if len(image_bytes) == 0:
                raise ValueError('Empty file provided')
            
            # Process OCR
            results = self._process_image_bytes(image_bytes)
            
            return {
                'filename': file.filename,
                'file_size': len(image_bytes),
                'full_text': self._extract_full_text(results),
                'detailed_results': results,
                'total_detections': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error processing uploaded image: {str(e)}")
            raise

    def process_image_base64(self, image_data: str) -> Dict[str, Any]:
        """
        Process base64 encoded image
        
        Args:
            image_data: Base64 encoded image string
            
        Returns:
            Dictionary with OCR results
        """
        try:
            # Clean base64 data
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Decode base64
            try:
                image_bytes = base64.b64decode(image_data)
            except Exception as e:
                raise ValueError(f'Invalid base64 data: {str(e)}')
            
            if len(image_bytes) == 0:
                raise ValueError('Empty image data')
            
            # Process OCR
            results = self._process_image_bytes(image_bytes)
            
            return {
                'data_size': len(image_bytes),
                'full_text': self._extract_full_text(results),
                'detailed_results': results,
                'total_detections': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error processing base64 image: {str(e)}")
            raise

    def process_batch(self, files) -> List[Dict[str, Any]]:
        """
        Process multiple files
        
        Args:
            files: List of Flask file objects
            
        Returns:
            List of dictionaries with OCR results
        """
        results = []
        
        for i, file in enumerate(files):
            try:
                if not file or file.filename == '':
                    results.append({
                        'file_index': i,
                        'filename': '',
                        'success': False,
                        'error': 'Empty file'
                    })
                    continue
                
                result = self.process_image_upload(file)
                result.update({
                    'file_index': i,
                    'success': True
                })
                results.append(result)
                
            except Exception as e:
                results.append({
                    'file_index': i,
                    'filename': file.filename if file else '',
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"Error processing file {i}: {str(e)}")
        
        return results

    def _process_image_bytes(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Internal method to process image bytes with EasyOCR
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            List of OCR results with text, confidence, and bounding boxes
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_np = np.array(image)
            
            # Perform OCR
            logger.info(f"Processing image of size: {image_np.shape}")
            ocr_results = self.reader.readtext(image_np)
            
            # Format results
            formatted_results = []
            for (bbox, text, confidence) in ocr_results:
                # Filter out low confidence results
                if confidence < 0.1:  # Adjust threshold as needed
                    continue
                    
                formatted_results.append({
                    'text': text.strip(),
                    'confidence': round(float(confidence), 4),
                    'bounding_box': {
                        'top_left': [round(float(bbox[0][0]), 2), round(float(bbox[0][1]), 2)],
                        'top_right': [round(float(bbox[1][0]), 2), round(float(bbox[1][1]), 2)],
                        'bottom_right': [round(float(bbox[2][0]), 2), round(float(bbox[2][1]), 2)],
                        'bottom_left': [round(float(bbox[3][0]), 2), round(float(bbox[3][1]), 2)]
                    }
                })
            
            logger.info(f"Found {len(formatted_results)} text regions")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            raise

    def _is_valid_image_file(self, filename: str) -> bool:
        """Check if file has valid image extension"""
        if not filename:
            return False
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
        return filename.lower().split('.')[-1] in allowed_extensions

    def _extract_full_text(self, results: List[Dict[str, Any]]) -> str:
        """Extract full text from OCR results"""
        if not results:
            return ""
        
        # Sort by vertical position (top to bottom)
        sorted_results = sorted(results, key=lambda x: x['bounding_box']['top_left'][1])
        
        # Join text with spaces
        return ' '.join([r['text'] for r in sorted_results if r['text'].strip()])

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.languages

    def get_engine_info(self) -> Dict[str, Any]:
        """Get engine information"""
        return {
            'languages': self.languages,
            'gpu_enabled': self.gpu,
            'engine': 'EasyOCR',
            'version': '1.7.2'
        }