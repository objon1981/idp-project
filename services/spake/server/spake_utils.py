"""
SPAKE (Simple Password-Authenticated Key Exchange) Protocol Implementation
This is a simplified implementation for educational/demonstration purposes.
For production use, consider using established cryptographic libraries.
"""

import hashlib
import secrets
import hmac
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import logging

logger = logging.getLogger(__name__)

class SPAKEError(Exception):
    """Custom exception for SPAKE protocol errors"""
    pass

class SPAKEServer:
    """
    SPAKE Server implementation using Elliptic Curve Cryptography
    """
    
    def __init__(self):
        """Initialize SPAKE server with curve parameters"""
        # Use SECP256R1 curve (P-256)
        self.curve = ec.SECP256R1()
        self.private_key = None
        self.public_key_bytes = None
        self.password_hash = None
        
        # SPAKE protocol constants (simplified)
        # In a real implementation, these would be standardized curve points
        self.M = self._generate_base_point("SPAKE_M")
        self.N = self._generate_base_point("SPAKE_N")
        
    def _generate_base_point(self, seed):
        """Generate a deterministic base point from seed"""
        # This is a simplified approach - real SPAKE uses standardized points
        seed_hash = hashlib.sha256(seed.encode()).digest()
        # Use the hash as a seed for point generation (simplified)
        return seed_hash[:32]  # Return 32 bytes for simplicity
    
    def _hash_password(self, password):
        """Hash the password using a strong hash function"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        # Use PBKDF2 with SHA-256
        salt = b"SPAKE_SALT"  # In production, use random salt per session
        return hashlib.pbkdf2_hmac('sha256', password, salt, 100000)
    
    def generate_public_key(self, password):
        """
        Generate server's public key for SPAKE protocol
        
        Args:
            password (str): Shared password
            
        Returns:
            bytes: Server's public key
        """
        try:
            # Hash the password
            self.password_hash = self._hash_password(password)
            
            # Generate private key
            self.private_key = ec.generate_private_key(self.curve)
            
            # Get the public key point
            public_key = self.private_key.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            
            # SPAKE protocol: add password-dependent offset
            # This is simplified - real SPAKE uses elliptic curve point arithmetic
            password_offset = self._compute_password_offset(self.password_hash, self.M)
            
            # Combine public key with password offset (simplified)
            self.public_key_bytes = self._xor_bytes(public_key_bytes, password_offset)
            
            logger.info("Server public key generated successfully")
            return self.public_key_bytes
            
        except Exception as e:
            logger.error(f"Error generating public key: {str(e)}")
            raise SPAKEError(f"Failed to generate public key: {str(e)}")
    
    def compute_shared_secret(self, client_public_key):
        """
        Compute shared secret from client's public key
        
        Args:
            client_public_key (bytes): Client's public key
            
        Returns:
            bytes: Shared secret
        """
        try:
            if self.private_key is None or self.password_hash is None:
                raise SPAKEError("Server not properly initialized")
            
            # Remove password offset from client's public key
            password_offset = self._compute_password_offset(self.password_hash, self.N)
            client_key_clean = self._xor_bytes(client_public_key, password_offset)
            
            # Reconstruct client's public key object (simplified)
            # In real implementation, this would involve proper EC point reconstruction
            try:
                client_public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(
                    self.curve, client_key_clean
                )
            except Exception:
                # Fallback: use the raw bytes for key derivation
                shared_point = client_key_clean
            else:
                # Perform ECDH
                shared_key = self.private_key.exchange(ec.ECDH(), client_public_key_obj)
                shared_point = shared_key
            
            # Derive final shared secret using HKDF
            shared_secret = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"SPAKE_SHARED_SECRET",
                info=b"SPAKE_KEY_DERIVATION"
            ).derive(shared_point[:32])  # Ensure we have enough bytes
            
            logger.info("Shared secret computed successfully")
            return shared_secret
            
        except Exception as e:
            logger.error(f"Error computing shared secret: {str(e)}")
            raise SPAKEError(f"Failed to compute shared secret: {str(e)}")
    
    def _compute_password_offset(self, password_hash, base_point):
        """Compute password-dependent offset"""
        # Simplified: combine password hash with base point
        combined = password_hash + base_point
        return hashlib.sha256(combined).digest()
    
    def _xor_bytes(self, a, b):
        """XOR two byte arrays (simplified mixing operation)"""
        # Ensure both arrays are the same length
        min_len = min(len(a), len(b))
        max_len = max(len(a), len(b))
        
        # Pad shorter array
        if len(a) < max_len:
            a = a + b'\x00' * (max_len - len(a))
        if len(b) < max_len:
            b = b + b'\x00' * (max_len - len(b))
        
        return bytes(x ^ y for x, y in zip(a, b))

class SPAKEClient:
    """
    SPAKE Client implementation for testing purposes
    """
    
    def __init__(self):
        """Initialize SPAKE client"""
        self.curve = ec.SECP256R1()
        self.private_key = None
        self.public_key_bytes = None
        self.password_hash = None
        
        # Same constants as server
        self.M = self._generate_base_point("SPAKE_M")
        self.N = self._generate_base_point("SPAKE_N")
    
    def _generate_base_point(self, seed):
        """Generate a deterministic base point from seed"""
        seed_hash = hashlib.sha256(seed.encode()).digest()
        return seed_hash[:32]
    
    def _hash_password(self, password):
        """Hash the password using the same method as server"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        salt = b"SPAKE_SALT"
        return hashlib.pbkdf2_hmac('sha256', password, salt, 100000)
    
    def generate_public_key(self, password):
        """Generate client's public key"""
        try:
            self.password_hash = self._hash_password(password)
            self.private_key = ec.generate_private_key(self.curve)
            
            public_key = self.private_key.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            
            # Add password offset (using N for client)
            password_offset = self._compute_password_offset(self.password_hash, self.N)
            self.public_key_bytes = self._xor_bytes(public_key_bytes, password_offset)
            
            return self.public_key_bytes
            
        except Exception as e:
            raise SPAKEError(f"Failed to generate client public key: {str(e)}")
    
    def compute_shared_secret(self, server_public_key):
        """Compute shared secret from server's public key"""
        try:
            if self.private_key is None or self.password_hash is None:
                raise SPAKEError("Client not properly initialized")
            
            # Remove password offset from server's public key
            password_offset = self._compute_password_offset(self.password_hash, self.M)
            server_key_clean = self._xor_bytes(server_public_key, password_offset)
            
            # Use the cleaned key for derivation
            shared_point = server_key_clean
            
            # Derive final shared secret
            shared_secret = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"SPAKE_SHARED_SECRET",
                info=b"SPAKE_KEY_DERIVATION"
            ).derive(shared_point[:32])
            
            return shared_secret
            
        except Exception as e:
            raise SPAKEError(f"Failed to compute shared secret: {str(e)}")
    
    def _compute_password_offset(self, password_hash, base_point):
        """Compute password-dependent offset"""
        combined = password_hash + base_point
        return hashlib.sha256(combined).digest()
    
    def _xor_bytes(self, a, b):
        """XOR two byte arrays"""
        min_len = min(len(a), len(b))
        max_len = max(len(a), len(b))
        
        if len(a) < max_len:
            a = a + b'\x00' * (max_len - len(a))
        if len(b) < max_len:
            b = b + b'\x00' * (max_len - len(b))
        
        return bytes(x ^ y for x, y in zip(a, b))

def verify_shared_secret(secret1, secret2):
    """Utility function to verify that two shared secrets match"""
    return hmac.compare_digest(secret1, secret2)

# Test function
def test_spake_protocol():
    """Test the SPAKE protocol implementation"""
    try:
        password = "test_password_123"
        
        # Create server and client
        server = SPAKEServer()
        client = SPAKEClient()
        
        # Generate public keys
        server_public = server.generate_public_key(password)
        client_public = client.generate_public_key(password)
        
        # Compute shared secrets
        server_secret = server.compute_shared_secret(client_public)
        client_secret = client.compute_shared_secret(server_public)
        
        # Verify they match
        if verify_shared_secret(server_secret, client_secret):
            print("SPAKE protocol test: SUCCESS")
            print(f"Shared secret: {server_secret.hex()}")
            return True
        else:
            print("SPAKE protocol test: FAILED - secrets don't match")
            return False
            
    except Exception as e:
        print(f"SPAKE protocol test: ERROR - {str(e)}")
        return False

if __name__ == "__main__":
    test_spake_protocol()