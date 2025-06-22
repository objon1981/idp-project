import pytest # type: ignore
import json
import io
from main import app
from ocr_engine import OCREngine

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def ocr_engine():
    """Create OCR engine instance"""
    return OCREngine()

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] in ['healthy', 'unhealthy']

def test_home_endpoint(client):
    """Test home endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'service' in data
    assert 'endpoints' in data

def test_ocr_upload_no_file(client):
    """Test OCR upload without file"""
    response = client.post('/ocr/upload')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_ocr_base64_no_data(client):
    """Test OCR base64 without data"""
    response = client.post('/ocr/base64', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_ocr_engine_initialization(ocr_engine):
    """Test OCR engine initialization"""
    assert ocr_engine.reader is not None
    assert ocr_engine.languages == ['en']

def test_valid_image_file():
    """Test image file validation"""
    engine = OCREngine()
    assert engine._is_valid_image_file('test.jpg') == True
    assert engine._is_valid_image_file('test.png') == True
    assert engine._is_valid_image_file('test.txt') == False
    assert engine._is_valid_image_file('') == False

def test_engine_info(ocr_engine):
    """Test engine info"""
    info = ocr_engine.get_engine_info()
    assert 'languages' in info
    assert 'gpu_enabled' in info
    assert 'engine' in info

# Run tests with: python -m pytest test_ocr.py -v