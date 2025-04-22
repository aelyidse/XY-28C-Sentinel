from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import hashlib
import json

class AuditSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class AuditRecord:
    operation: str
    timestamp: float
    user_id: str
    role: str
    resource: str
    action: str
    status: str
    details: Dict[str, Any]
    severity: AuditSeverity
    component_id: str
    previous_hash: str
    signature: bytes

class AuditLogger:
    def __init__(self, blockchain_network, secure_storage):
        self.blockchain = blockchain_network
        self.storage = secure_storage
        self.last_hash = None
    
    async def log_operation(
        self,
        operation: str,
        user_id: str,
        role: str,
        resource: str,
        action: str,
        status: str,
        details: Dict[str, Any],
        severity: AuditSeverity,
        component_id: str
    ) -> None:
        """Log a sensitive operation with full context"""
        
        # Create audit record
        record = AuditRecord(
            operation=operation,
            timestamp=datetime.now().timestamp(),
            user_id=user_id,
            role=role,
            resource=resource,
            action=action,
            status=status,
            details=details,
            severity=severity,
            component_id=component_id,
            previous_hash=self.last_hash or "",
            signature=b""
        )
        
        # Calculate record hash
        record_hash = self._calculate_hash(record)
        
        # Sign the record
        record.signature = self._sign_record(record_hash)
        
        # Store locally
        await self.storage.store_audit_record(record)
        
        # Add to blockchain for immutability
        await self.blockchain.add_audit_record({
            "type": "audit_record",
            "hash": record_hash.hex(),
            "record": self._serialize_record(record)
        })
        
        # Update last hash
        self.last_hash = record_hash
        
    def _calculate_hash(self, record: AuditRecord) -> bytes:
        """Calculate cryptographic hash of audit record"""
        record_dict = self._serialize_record(record)
        return hashlib.sha256(json.dumps(record_dict).encode()).digest()
        
    def _sign_record(self, record_hash: bytes) -> bytes:
        """Sign audit record hash with system private key"""
        # Implementation depends on crypto system used
        return b"" # Placeholder
        
    def _serialize_record(self, record: AuditRecord) -> Dict:
        """Convert audit record to serializable dict"""
        return {
            "operation": record.operation,
            "timestamp": record.timestamp,
            "user_id": record.user_id,
            "role": record.role,
            "resource": record.resource,
            "action": record.action,
            "status": record.status,
            "details": record.details,
            "severity": record.severity.value,
            "component_id": record.component_id,
            "previous_hash": record.previous_hash
        }