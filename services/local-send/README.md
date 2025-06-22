# Local Send Service

A secure, password-authenticated file transfer service using SPAKE2 (Simple Password-Authenticated Key Exchange) protocol. This Flask-based service enables secure peer-to-peer file transfers without requiring pre-shared certificates or complex key management.

## Features

- **SPAKE2 Protocol**: Password-authenticated key exchange for secure communication
- **Flask REST API**: Clean, well-documented API endpoints
- **Secure File Transfer**: End-to-end encryption using AES-256-GCM
- **Session Management**: Temporary sessions with automatic cleanup
- **File Integrity**: SHA-256 hash verification for uploaded files
- **Docker Support**: Containerized deployment ready
- **Comprehensive Testing**: Full test suite with pytest

## Security Features

- Password-authenticated key exchange (SPAKE2)
- AES-256-GCM encryption for file data
- Verification codes for session joining
- File type validation and sanitization
- Automatic session cleanup
- No permanent key storage

## Quick Start

### Local Development

1. **Clone and setup**:
```bash
cd idp-project-new/services/local-send/app
pip install -r requirements.txt
```

2. **Run the service**:
```bash
python main.py
```

3. **Test the API**:
```bash
curl http://localhost:5000/health
```

### Docker Deployment

1. **Build the image**:
```bash
docker build -t local-send-service .
```

2. **Run the container**:
```bash
docker run -p 5000:5000 local-send-service
```

## API Documentation

### Authentication Flow

1. **Create Session**: One party creates a session with a password
2. **Join Session**: Another party joins using the session ID, verification code, and same password
3. **SPAKE2 Exchange**: Both parties exchange public keys and derive shared secret
4. **Secure Transfer**: Files are transferred with encryption

### Core Endpoints

#### Health Check
```http
GET /health
```

#### Create Session
```http
POST /api/session/create
Content-Type: application/json

{
    "password": "your_secure_password"
}
```

**Response**:
```json
{
    "session_id": "a1b2c3d4",
    "verification_code": "123456",
    "public_key": "04a1b2c3...",
    "status": "created"
}
```

#### Join Session
```http
POST /api/session/{session_id}/join
Content-Type: application/json

{
    "password": "your_secure_password",
    "public_key": "04d4c3b2...",
    "verification_code": "123456"
}
```

#### Upload File
```http
POST /api/session/{session_id}/upload
Content-Type: multipart/form-data

file: (binary file data)
```

#### List Files
```http
GET /api/session/{session_id}/files
```

#### Download File
```http
GET /api/session/{session_id}/download/{file_id}
```

#### Session Status
```http
GET /api/session/{session_id}/status
```

#### Close Session
```http
POST /api/session/{session_id}/close
```

## SPAKE2 Implementation

### Best Version Recommendation

**Recommended**: Use the included `cryptography` library implementation (already integrated in `spake_utils.py`).

### Why This Implementation?

1. **Production Ready**: Uses the `cryptography` library which is:
   - FIPS 140-2 validated implementations
   - Regularly audited and maintained
   - Industry standard for Python cryptography

2. **Secure by Design**:
   - NIST P-256 elliptic curve
   - HKDF for key derivation
   - AES-256-GCM for encryption
   - Constant-time operations

3. **Well Tested**: Comprehensive test suite covering:
   - Key exchange scenarios
   - Encryption/decryption
   - Error conditions
   - Security edge cases

### Alternative SPAKE2 Libraries

If you need a different implementation, consider:

1. **spake2** (PyPI package):
   ```bash
   pip install spake2
   ```
   - Simpler API
   - Smaller footprint
   - Less battle-tested

2. **pynacl** with custom SPAKE2:
   ```bash
   pip install pynacl
   ```
   - Curve25519 based
   - Requires custom SPAKE2 implementation

3. **cryptg** (Telegram's implementation):
   - High performance
   - Limited documentation

**Recommendation**: Stick with the current `cryptography`-based implementation for production use.

## Usage Examples

### Python Client Example

```python
import requests
import json

# Create session
response = requests.post('http://localhost:5000/api/session/create', 
                        json={'password': 'secure_password_123'})
session_data = response.json()

session_id = session_data['session_id']
verification_code = session_data['verification_code']

print(f"Session created: {session_id}")
print(f"Share this code: {verification_code}")

# Upload file
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(f'http://localhost:5000/api/session/{session_id}/upload', 
                           files=files)
    upload_data = response.json()
    print(f"File uploaded: {upload_data}")
```

### JavaScript Client Example

```javascript
// Create session
const createSession = async (password) => {
    const response = await fetch('/api/session/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password})
    });
    return await response.json();
};

// Upload file
const uploadFile = async (sessionId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`/api/session/${sessionId}/upload`, {
        method: 'POST',
        body: formData
    });
    return await response.json();
};
```

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-flask requests

# Run all tests
python test_local_send.py

# Run with pytest for detailed output
pytest test_local_send.py -v

# Run specific test categories
pytest test_local_send.py::TestSPAKE2 -v
pytest test_local_send.py::TestFlaskAPI -v
pytest test_local_send.py::TestSecurity -v
```

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `production` for production deployment
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 100MB)
- `UPLOAD_FOLDER`: Directory for temporary file storage
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)

### Production Considerations

1. **Use Redis**: Replace in-memory storage with Redis for scalability
2. **Add Rate Limiting**: Implement rate limiting to prevent abuse
3. **SSL/TLS**: Always use HTTPS in production
4. **File Cleanup**: Implement robust file cleanup mechanisms
5. **Monitoring**: Add proper logging and monitoring
6. **Load Balancing**: Use multiple workers with gunicorn

## Security Considerations

1. **Password Strength**: Encourage strong passwords
2. **Session Limits**: Implement maximum concurrent sessions
3. **File Size Limits**: Enforce reasonable file size limits
4. **File Type Validation**: Restrict allowed file types
5. **Network Security**: Use behind reverse proxy with proper headers
6. **Regular Updates**: Keep dependencies updated

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Client A      │    │   Client B      │
│                 │    │                 │
│ 1. Create       │    │ 2. Join         │
│    Session      │    │    Session      │
│                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │   SPAKE2 Exchange    │
          │ ◄──────────────────► │
          │                      │
          │    Flask Service     │
          │ ┌─────────────────┐  │
          └►│  Session Mgmt   │◄─┘
            │  File Storage   │
            │  SPAKE2 Handler │
            └─────────────────┘
```

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with your organization's security policies before production use.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
1. Check the test suite for usage examples
2. Review the API documentation above
3. Examine the SPAKE2 implementation in `spake_utils.py`