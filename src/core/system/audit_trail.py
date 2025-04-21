from dataclasses import dataclass
from typing import Dict, Any
import hashlib
import json
from datetime import datetime

@dataclass
class AuditEntry:
    event_type: str
    component_id: str
    data: Dict[str, Any]
    timestamp: float
    previous_hash: str
    signature: bytes

class AuditTrailManager:
    def __init__(self, blockchain: CommandBlockchain):
        self.blockchain = blockchain
        self.entries = []
        
    async def log_event(self, event: SystemEvent) -> None:
        """Create and store an immutable audit entry"""
        entry = AuditEntry(
            event_type=event.event_type,
            component_id=event.component_id,
            data=event.data,
            timestamp=event.timestamp,
            previous_hash=self._get_last_entry_hash(),
            signature=b''  # Will be signed
        )
        
        # Sign the entry
        signed_entry = self._sign_entry(entry)
        
        # Add to blockchain
        tx = self.blockchain.create_transaction({
            'type': 'audit_entry',
            'entry': signed_entry
        })
        self.blockchain.add_block(tx)
        
        # Store locally
        self.entries.append(signed_entry)

    def _get_last_entry_hash(self) -> str:
        """Get hash of last audit entry"""
        if not self.entries:
            return "genesis"
        last_entry = self.entries[-1]
        return hashlib.sha256(
            f"{last_entry.event_type}{last_entry.timestamp}".encode()
        ).hexdigest()

    def _sign_entry(self, entry: AuditEntry) -> AuditEntry:
        """Sign audit entry with node private key"""
        private_key = self.blockchain.node_keys['uav']
        entry_data = f"{entry.event_type}{entry.component_id}{json.dumps(entry.data)}{entry.timestamp}"
        entry.signature = private_key.sign(
            entry_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return entry

    async def verify_audit_trail(self) -> bool:
        """Verify integrity of audit trail"""
        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i-1]
            
            # Check hash continuity
            if current.previous_hash != self._calculate_entry_hash(previous):
                return False
                
            # Verify signature
            if not self._verify_entry_signature(current):
                return False
                
        return True

    def _calculate_entry_hash(self, entry: AuditEntry) -> str:
        """Calculate hash of audit entry"""
        return hashlib.sha256(
            f"{entry.event_type}{entry.component_id}{entry.timestamp}".encode()
        ).hexdigest()

    def _verify_entry_signature(self, entry: AuditEntry) -> bool:
        """Verify entry signature"""
        public_key = self.blockchain.node_keys['uav'].public_key()
        entry_data = f"{entry.event_type}{entry.component_id}{json.dumps(entry.data)}{entry.timestamp}"
        try:
            public_key.verify(
                entry.signature,
                entry_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False