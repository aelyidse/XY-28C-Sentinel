import hashlib
from typing import Dict, List
from cryptography.hazmat.primitives import serialization
from ..comms.secure_comms import SecureCommunication

class OTAUpdater:
    def __init__(self, secure_comms: SecureCommunication):
        self.secure_comms = secure_comms
        self.update_queue = []
        
    async def check_for_updates(self) -> List[Dict]:
        """Check for available updates from secure server"""
        update_list = await self.secure_comms.request_updates()
        return [
            update for update in update_list 
            if self._validate_update_signature(update)
        ]
        
    async def apply_update(self, update: Dict) -> bool:
        """Apply verified update package"""
        if not self._verify_update_integrity(update):
            return False
            
        # Stage update for next maintenance window
        self.update_queue.append(update)
        return True
        
    def _validate_update_signature(self, update: Dict) -> bool:
        """Validate cryptographic signature of update package"""
        try:
            public_key = serialization.load_pem_public_key(update['signature_key'])
            public_key.verify(
                update['signature'],
                update['payload'],
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False