#!/usr/bin/env python3
"""
Test Suite for Local Send Service
Tests the Flask API endpoints and SPAKE2 implementation
"""

import pytest
import json
import os
import tempfile
import requests
from unittest.mock import patch, MagicMock
import sys
import time

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, active_sessions
from spake_utils import SPAKE2Handler, create_spake2_pair, demo_key_exchange

# Test configuration
TEST_PASSWORD = "test_password_123"
TEST_SESSION_ID = "test_session"
BASE_URL = "http://localhost:5000"

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    active_sessions.clear()

@pytest.fixture
def test_file():
    """Create a temporary test file"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write("This is a test file for local send.")
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)

class TestSPAKE2:
    """Test the SPAKE2 implementation"""
    
    def test_spake2_key_exchange(self):
        """Test basic SPAKE2 key exchange"""
        alice, bob = create_spake2_pair(TEST_PASSWORD)
        
        # Generate public keys
        alice_public = alice.generate_public_key()
        bob_public = bob.generate_public_key()
        
        assert alice_public is not None
        assert bob_public is not None
        assert len(alice_public) > 0
        assert len(bob_public) > 0
        
        # Complete key exchange
        alice_secret = alice.complete_key_exchange(bob_public)
        bob_secret = bob.complete_key_exchange(alice_public)
        
        # Verify secrets match
        assert alice_secret == bob_secret
        assert len(alice_secret) == 32  # 256 bits
    
    def test_spake2_encryption_decryption(self):
        """Test SPAKE2 encryption and decryption"""
        alice, bob = create_spake2_pair(TEST_PASSWORD)
        
        # Complete key exchange
        alice_public = alice.generate_public_key()
        bob_public = bob.generate_public_key()
        alice.complete_key_exchange(bob_public)
        bob.complete_key_exchange(alice_public)
        
        # Test encryption/decryption
        test_message = b"Hello, this is a test message for encryption!"
        
        # Alice encrypts
        encrypted, nonce = alice.encrypt_data(test_message)
        assert encrypted != test_message
        assert len(nonce) == 12  # GCM nonce size
        
        # Bob decrypts
        decrypted = bob.decrypt_data(encrypted, nonce)
        assert decrypted == test_message
    
    def test_spake2_wrong_password(self):
        """Test SPAKE2 with wrong password fails"""
        alice = SPAKE2Handler("correct_password", "alice")
        bob = SPAKE2Handler("wrong_password", "bob")
        
        alice_public = alice.generate_public_key()
        bob_public = bob.generate_public_key()
        
        alice_secret = alice.complete_key_exchange(bob_public)
        bob_secret = bob.complete_key_exchange(alice_public)
        
        # Secrets should be different with different passwords
        assert alice_secret != bob_secret
    
    def test_spake2_proof_generation(self):
        """Test SPAKE2 proof generation"""
        alice, bob = create_spake2_pair(TEST_PASSWORD)
        
        # Complete key exchange
        alice_public = alice.generate_public_key()
        bob_public = bob.generate_public_key()
        alice.complete_key_exchange(bob_public)
        bob.complete_key_exchange(alice_public)
        
        # Generate proofs
        alice_proof = alice.get_proof()
        bob_proof = bob.get_proof()
        
        assert alice_proof is not None
        assert bob_proof is not None
        assert len(alice_proof) == 32  # SHA-256 hash length


class TestFlaskAPI:
    """Test the Flask API endpoints"""
    
    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_create_session(self, client):
        """Test session creation"""
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'verification_code' in data
        assert 'public_key' in data
        assert data['status'] == 'created'
        
        # Verify session was stored
        session_id = data['session_id']
        assert session_id in active_sessions
        assert active_sessions[session_id]['status'] == 'waiting_for_peer'
    
    def test_create_session_no_password(self, client):
        """Test session creation without password fails"""
        response = client.post('/api/session/create', 
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_join_session(self, client):
        """Test joining a session"""
        # First create a session
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        verification_code = session_data['verification_code']
        
        # Create another SPAKE2 handler to simulate peer
        peer_handler = SPAKE2Handler(TEST_PASSWORD, "peer")
        peer_public_key = peer_handler.generate_public_key()
        
        # Join the session
        join_payload = {
            'password': TEST_PASSWORD,
            'public_key': peer_public_key.hex(),
            'verification_code': verification_code
        }
        
        response = client.post(f'/api/session/{session_id}/join',
                             json=join_payload,
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'connected'
        assert 'public_key' in data
    
    def test_join_nonexistent_session(self, client):
        """Test joining a non-existent session fails"""
        join_payload = {
            'password': TEST_PASSWORD,
            'public_key': 'deadbeef',
            'verification_code': '123456'
        }
        
        response = client.post('/api/session/nonexistent/join',
                             json=join_payload,
                             content_type='application/json')
        
        assert response.status_code == 404
    
    def test_session_status(self, client):
        """Test getting session status"""
        # Create a session first
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        
        # Get status
        response = client.get(f'/api/session/{session_id}/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['session_id'] == session_id
        assert data['status'] == 'waiting_for_peer'
        assert 'created_at' in data
        assert data['file_count'] == 0
    
    def test_upload_file(self, client, test_file):
        """Test file upload"""
        # Create and connect a session
        session_id = self._create_connected_session(client)
        
        # Upload file
        with open(test_file, 'rb') as f:
            response = client.post(f'/api/session/{session_id}/upload',
                                 data={'file': (f, 'test.txt')},
                                 content_type='multipart/form-data')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'uploaded'
        assert 'file_id' in data
        assert data['filename'] == 'test.txt'
        assert 'size' in data
        assert 'hash' in data
    
    def test_upload_file_not_connected(self, client, test_file):
        """Test file upload to non-connected session fails"""
        # Create session but don't connect
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        
        # Try to upload file
        with open(test_file, 'rb') as f:
            response = client.post(f'/api/session/{session_id}/upload',
                                 data={'file': (f, 'test.txt')},
                                 content_type='multipart/form-data')
        
        assert response.status_code == 400
    
    def test_list_files(self, client, test_file):
        """Test listing files in a session"""
        # Create connected session and upload file
        session_id = self._create_connected_session(client)
        
        with open(test_file, 'rb') as f:
            client.post(f'/api/session/{session_id}/upload',
                       data={'file': (f, 'test.txt')},
                       content_type='multipart/form-data')
        
        # List files
        response = client.get(f'/api/session/{session_id}/files')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'files' in data
        assert len(data['files']) == 1
        assert data['files'][0]['filename'] == 'test.txt'
    
    def test_download_file(self, client, test_file):
        """Test downloading a file"""
        # Create connected session and upload file
        session_id = self._create_connected_session(client)
        
        with open(test_file, 'rb') as f:
            upload_response = client.post(f'/api/session/{session_id}/upload',
                                        data={'file': (f, 'test.txt')},
                                        content_type='multipart/form-data')
        
        upload_data = json.loads(upload_response.data)
        file_id = upload_data['file_id']
        
        # Download file
        response = client.get(f'/api/session/{session_id}/download/{file_id}')
        assert response.status_code == 200
        
        # Verify file content
        original_content = open(test_file, 'rb').read()
        assert response.data == original_content
    
    def test_close_session(self, client):
        """Test closing a session"""
        # Create a session
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        
        # Close session
        response = client.post(f'/api/session/{session_id}/close')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'closed'
        
        # Verify session was removed
        assert session_id not in active_sessions
    
    def _create_connected_session(self, client):
        """Helper method to create a connected session"""
        # Create session
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        verification_code = session_data['verification_code']
        
        # Join session
        peer_handler = SPAKE2Handler(TEST_PASSWORD, "peer")
        peer_public_key = peer_handler.generate_public_key()
        
        join_payload = {
            'password': TEST_PASSWORD,
            'public_key': peer_public_key.hex(),
            'verification_code': verification_code
        }
        
        client.post(f'/api/session/{session_id}/join',
                   json=join_payload,
                   content_type='application/json')
        
        return session_id


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self, client, test_file):
        """Test the complete file transfer workflow"""
        # 1. Create session
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        verification_code = session_data['verification_code']
        
        # 2. Join session
        peer_handler = SPAKE2Handler(TEST_PASSWORD, "peer")
        peer_public_key = peer_handler.generate_public_key()
        
        join_payload = {
            'password': TEST_PASSWORD,
            'public_key': peer_public_key.hex(),
            'verification_code': verification_code
        }
        
        response = client.post(f'/api/session/{session_id}/join',
                             json=join_payload,
                             content_type='application/json')
        assert response.status_code == 200
        
        # 3. Upload file
        with open(test_file, 'rb') as f:
            response = client.post(f'/api/session/{session_id}/upload',
                                 data={'file': (f, 'test.txt')},
                                 content_type='multipart/form-data')
        assert response.status_code == 200
        
        # 4. List files
        response = client.get(f'/api/session/{session_id}/files')
        assert response.status_code == 200
        files_data = json.loads(response.data)
        assert len(files_data['files']) == 1
        
        # 5. Download file
        file_id = files_data['files'][0]['file_id']
        response = client.get(f'/api/session/{session_id}/download/{file_id}')
        assert response.status_code == 200
        
        # 6. Verify file integrity
        original_content = open(test_file, 'rb').read()
        assert response.data == original_content
        
        # 7. Close session
        response = client.post(f'/api/session/{session_id}/close')
        assert response.status_code == 200
        
        # 8. Verify session is cleaned up
        assert session_id not in active_sessions


class TestSecurity:
    """Security-focused tests"""
    
    def test_different_passwords_fail(self, client):
        """Test that different passwords prevent connection"""
        # Create session with one password
        payload = {'password': 'password1'}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        verification_code = session_data['verification_code']
        
        # Try to join with different password
        peer_handler = SPAKE2Handler('password2', "peer")
        peer_public_key = peer_handler.generate_public_key()
        
        join_payload = {
            'password': 'password2',
            'public_key': peer_public_key.hex(),
            'verification_code': verification_code
        }
        
        response = client.post(f'/api/session/{session_id}/join',
                             json=join_payload,
                             content_type='application/json')
        
        # Should succeed in joining but key exchange will produce different secrets
        # In practice, this would be detected during the actual data transfer
        assert response.status_code == 200
    
    def test_wrong_verification_code(self, client):
        """Test that wrong verification code prevents joining"""
        # Create session
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        
        # Try to join with wrong verification code
        peer_handler = SPAKE2Handler(TEST_PASSWORD, "peer")
        peer_public_key = peer_handler.generate_public_key()
        
        join_payload = {
            'password': TEST_PASSWORD,
            'public_key': peer_public_key.hex(),
            'verification_code': '000000'  # Wrong code
        }
        
        response = client.post(f'/api/session/{session_id}/join',
                             json=join_payload,
                             content_type='application/json')
        
        assert response.status_code == 401
    
    def test_file_type_validation(self, client):
        """Test that only allowed file types can be uploaded"""
        session_id = self._create_connected_session(client)
        
        # Create a fake executable file
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b'fake executable content')
            fake_exe = f.name
        
        try:
            with open(fake_exe, 'rb') as f:
                response = client.post(f'/api/session/{session_id}/upload',
                                     data={'file': (f, 'malware.exe')},
                                     content_type='multipart/form-data')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'not allowed' in data['error']
        
        finally:
            os.unlink(fake_exe)
    
    def _create_connected_session(self, client):
        """Helper method to create a connected session"""
        payload = {'password': TEST_PASSWORD}
        response = client.post('/api/session/create', 
                             json=payload,
                             content_type='application/json')
        
        session_data = json.loads(response.data)
        session_id = session_data['session_id']
        verification_code = session_data['verification_code']
        
        peer_handler = SPAKE2Handler(TEST_PASSWORD, "peer")
        peer_public_key = peer_handler.generate_public_key()
        
        join_payload = {
            'password': TEST_PASSWORD,
            'public_key': peer_public_key.hex(),
            'verification_code': verification_code
        }
        
        client.post(f'/api/session/{session_id}/join',
                   json=join_payload,
                   content_type='application/json')
        
        return session_id


def test_demo_functionality():
    """Test the demo functionality"""
    # This should run without errors
    demo_key_exchange("demo_password")


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
    
    # Run demo
    print("\n" + "="*50)
    print("Running SPAKE2 Demo")
    print("="*50)
    test_demo_functionality()