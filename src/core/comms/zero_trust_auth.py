from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
import os
import time

class ZeroTrustAuth:
    def __init__(self, blockchain: CommandBlockchain):
        self.blockchain = blockchain
        self.session_keys = {}
        self.auth_timeout = 300  # 5 minutes
        
    def generate_challenge(self) -> tuple[bytes, bytes]:
        """Generate authentication challenge"""
        nonce = os.urandom(32)
        timestamp = str(time.time()).encode()
        return nonce, timestamp
        
    def verify_response(self, node_id: str, challenge: bytes, response: bytes) -> bool:
        """Verify authentication response"""
        # Get node's public key
        public_key = self.blockchain.node_keys[node_id].public_key()
        
        try:
            # Verify signature
            public_key.verify(
                response,
                challenge,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
            
    def generate_session_key(self, node_id: str) -> bytes:
        """Generate ephemeral session key"""
        # Derive key using HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'session_key'
        )
        self.session_keys[node_id] = hkdf.derive(os.urandom(32))
        return self.session_keys[node_id]
        
    def verify_session_key(self, node_id: str, key: bytes) -> bool:
        """Verify session key"""
        return self.session_keys.get(node_id) == key
        
    def rotate_keys(self) -> None:
        """Rotate authentication keys"""
        # Generate new key pairs for all nodes
        self.blockchain._generate_node_keys()