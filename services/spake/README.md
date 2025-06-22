# SPAKE Service

A Flask-based implementation of the SPAKE (Simple Password-Authenticated Key Exchange) protocol for secure key exchange between parties sharing a common password.

## Overview

This service provides REST API endpoints for implementing the SPAKE protocol, allowing two parties to establish a shared secret key using only a common password, without transmitting the password over the network.

## Features

- **Password-Authenticated Key Exchange**: Secure key derivation using shared passwords
- **REST API**: Simple HTTP endpoints for integration
- **Session Management**: Track multiple concurrent SPAKE sessions
- **Error Handling**: Comprehensive error handling and logging
- **Health Monitoring**: Health check endpoint for service monitoring
- **Docker Support**: Containerized deployment ready

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Initiate SPAKE Protocol
```
POST /spake/initiate
Content-Type: application/json

{
    "session_id": "unique_session_identifier",
    "password": "shared_password"
}
```

Response:
```json
{
    "session_id": "unique_session_identifier",
    "public_key": "hex_encoded_server_public_key",
    "status": "initiated"
}
```

### Exchange Keys
```
POST /spake/exchange
Content-Type: application/json

{
    "session_id": "unique_session_identifier",
    "client_public_key": "hex_encoded_client_public_key"
}
```

Response:
```json
{
    "session_id": "unique_session_identifier",
    "shared_secret": "hex_encoded_shared_secret",
    "status": "completed"
}
```

### Get Session Status
```
GET /spake/status/<session_id>
```

Response:
```json
{
    "session_id": "session_id",
    "status": "initiated|completed"
}
```

### Cleanup Session
```
DELETE /spake/cleanup/<session_id>
```

Response:
```json
{
    "session_id": "session_id",
    "message": "Session cleaned up successfully"
}
```

### List Active Sessions
```
GET /spake/sessions
```

Response:
```json
{
    "active_sessions": 2,
    "sessions": [
        {
            "session_id": "session1",
            "status": "initiated"
        },
        {
            "session_id": "session2",
            "status": "completed"
        }
    ]
}
```

## Installation & Setup

### Local Development

1. **Install Python Dependencies**:
   ```bash
   cd server/
   pip install -r requirements.txt
   ```

2. **Run the Service**:
   ```bash
   python main.py
   ```

   The service will start on `http://localhost:5000`

3. **Environment Variables**:
   - `PORT`: Service port (default: 5000)
   - `FLASK_DEBUG`: Enable debug mode (default: False)

### Docker Deployment

1. **Build the Docker Image**:
   ```bash
   docker build -t spake-service .
   ```

2. **Run the Container**:
   ```bash
   docker run -p 5000:5000 spake-service
   ```

3. **Using Docker Compose** (example):
   ```yaml
   version: '3.8'
   services:
     spake:
       build: .
       ports:
         - "5000:5000"
       environment:
         - FLASK_ENV=production
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
         interval: 30s
         timeout: 10s
         retries: 3
   ```

## Usage Example

### Using curl

1. **Initiate SPAKE session**:
   ```bash
   curl -X POST http://localhost:5000/spake/initiate \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test123", "password": "mypassword"}'
   ```

2. **Exchange keys** (assuming you have a client public key):
   ```bash
   curl -X POST http://localhost:5000/spake/exchange \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test123", "client_public_key": "client_key_hex"}'
   ```

### Python Client Example

```python
import requests
from spake_utils import SPAKEClient

# Initialize client
client = SPAKEClient()
password = "shared_password"
session_id = "test_session"

# Generate client public key
client_public_key = client.generate_public_key(password)

# Initiate server session
response = requests.post('http://localhost:5000/spake/initiate', json={
    'session_id': session_id,
    'password': password
})
server_data = response.json()
server_public_key = bytes.fromhex(server_data['public_key'])

# Exchange keys
response = requests.post('http://localhost:5000/spake/exchange', json={
    'session_id': session_id,
    'client_public_key': client_public_key.hex()
})
exchange_data = response.json()

# Compute client-side shared secret
client_shared_secret = client.compute_shared_secret(server_public_key)
server_shared_secret = bytes.fromhex(exchange_data['shared_secret'])

# Verify secrets match
print(f"Secrets match: {client_shared_secret == server_shared_secret}")
```

## Security Considerations

⚠️ **Important**: This is a simplified implementation for educational/demonstration purposes.

For production use:
- Use established cryptographic libraries (e.g., `cryptg`, `pycryptodome`)
- Implement proper session timeouts and cleanup
- Use secure random number generation
- Add rate limiting and authentication
- Store sessions in secure, persistent storage (Redis, database)
- Implement proper logging and monitoring
- Use TLS/HTTPS for all communications
- Follow OWASP security guidelines

## Protocol Details

This implementation uses a simplified version of SPAKE:
- **Elliptic Curve**: SECP256R1 (P-256)
- **Hash Function**: SHA-256 with PBKDF2
- **Key Derivation**: HKDF with SHA-256

The protocol flow:
1. Both parties derive a password hash using PBKDF2
2. Each party generates an EC key pair
3. Public keys are masked with password-dependent offsets
4. Parties exchange masked public keys
5. Each party removes the password offset from the received key
6. Shared secret is derived using ECDH + HKDF

## Testing

Run the built-in protocol test:
```bash
cd server/
python spake_utils.py
```

## Error Handling

The service includes comprehensive error handling:
- **400 Bad Request**: Invalid input data
- **404 Not Found**: Session not found
- **409 Conflict**: Session already exists
- **500 Internal Server Error**: Unexpected errors

All errors are logged with appropriate detail levels.

## Monitoring

- Health check endpoint: `GET /health`
- Session listing: `GET /spake/sessions`
- Comprehensive logging with configurable levels

## Contributing

1. Follow PEP 8 style guidelines
2. Add appropriate error handling
3. Include unit tests for new features
4. Update documentation for API changes

## License

This implementation is provided for educational purposes. Please ensure compliance with your organization's security policies before production use.