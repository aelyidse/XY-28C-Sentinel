from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import asyncio
from ..communication.secure_manager import SecureCommunicationManager
from ..system.events import SystemEvent, SystemEventType

@dataclass
class SecurityAnomaly:
    timestamp: float
    anomaly_type: str
    severity: int  # 0-10
    details: Dict[str, Any]
    source_id: str

class AntiHijackManager:
    def __init__(self, secure_comm: SecureCommunicationManager):
        self.secure_comm = secure_comm
        self.anomaly_threshold = 7
        self.command_history = []
        self.behavioral_baseline = {}
        self.active_countermeasures = set()
        
    async def monitor_commands(self, command: Dict[str, Any]) -> bool:
        """Monitor and validate incoming commands for hijacking attempts"""
        # Calculate command hash for tracking
        command_hash = hashlib.sha256(str(command).encode()).hexdigest()
        
        # Check command against behavioral patterns
        anomaly = await self._detect_behavioral_anomalies(command)
        if anomaly:
            await self._handle_anomaly(anomaly)
            return False
            
        # Validate command frequency
        if not self._validate_command_frequency(command):
            await self._handle_anomaly(SecurityAnomaly(
                timestamp=datetime.now().timestamp(),
                anomaly_type="excessive_commands",
                severity=8,
                details={"command_hash": command_hash},
                source_id=command.get("source", "unknown")
            ))
            return False
            
        # Update command history
        self.command_history.append({
            "timestamp": datetime.now().timestamp(),
            "command": command,
            "hash": command_hash
        })
        
        return True
        
    async def _detect_behavioral_anomalies(self, command: Dict[str, Any]) -> Optional[SecurityAnomaly]:
        """Detect anomalous command patterns"""
        # Check command type frequency
        cmd_type = command.get("type", "unknown")
        if self._is_anomalous_frequency(cmd_type):
            return SecurityAnomaly(
                timestamp=datetime.now().timestamp(),
                anomaly_type="unusual_pattern",
                severity=7,
                details={"command_type": cmd_type},
                source_id=command.get("source", "unknown")
            )
            
        # Check parameter ranges
        if not self._validate_parameter_ranges(command):
            return SecurityAnomaly(
                timestamp=datetime.now().timestamp(),
                anomaly_type="invalid_parameters",
                severity=8,
                details={"command": command},
                source_id=command.get("source", "unknown")
            )
            
        return None
        
    def _is_anomalous_frequency(self, cmd_type: str) -> bool:
        """Check if command frequency is anomalous"""
        recent_commands = [cmd["command"].get("type") for cmd in self.command_history[-50:]]
        type_frequency = recent_commands.count(cmd_type)
        return type_frequency > self.anomaly_threshold
        
    def _validate_parameter_ranges(self, command: Dict[str, Any]) -> bool:
        """Validate command parameters against allowed ranges"""
        if command.get("type") == "navigation":
            return self._validate_navigation_params(command.get("parameters", {}))
        elif command.get("type") == "system":
            return self._validate_system_params(command.get("parameters", {}))
        return True
        
    def _validate_navigation_params(self, params: Dict[str, Any]) -> bool:
        """Validate navigation command parameters"""
        if "altitude" in params:
            if not (0 <= params["altitude"] <= 30000):  # meters
                return False
        if "speed" in params:
            if not (0 <= params["speed"] <= 1000):  # m/s
                return False
        return True
        
    def _validate_system_params(self, params: Dict[str, Any]) -> bool:
        """Validate system command parameters"""
        restricted_commands = {"shutdown", "reset", "firmware_update"}
        if params.get("action") in restricted_commands:
            return False
        return True
        
    async def _handle_anomaly(self, anomaly: SecurityAnomaly) -> None:
        """Handle detected security anomalies"""
        # Log anomaly
        await self._log_security_event(anomaly)
        
        # Implement countermeasures based on severity
        if anomaly.severity >= 8:
            await self._activate_emergency_protocols(anomaly)
        elif anomaly.severity >= 5:
            await self._implement_defensive_measures(anomaly)
            
    async def _log_security_event(self, anomaly: SecurityAnomaly) -> None:
        """Log security anomaly event"""
        await self.secure_comm.send_secure_message(
            message={
                "type": "security_alert",
                "anomaly": anomaly.__dict__,
                "timestamp": datetime.now().timestamp()
            },
            recipient="ground_control"
        )
        
    async def _activate_emergency_protocols(self, anomaly: SecurityAnomaly) -> None:
        """Activate emergency security protocols"""
        # Implement immediate defensive measures
        self.active_countermeasures.add("command_lockdown")
        self.active_countermeasures.add("emergency_beacon")
        
        # Switch to backup communication channels
        await self.secure_comm.blockchain.broadcast_block({
            "type": "emergency_protocol",
            "protocol": "backup_comms",
            "reason": anomaly.__dict__
        })
        
    async def _implement_defensive_measures(self, anomaly: SecurityAnomaly) -> None:
        """Implement defensive security measures"""
        if anomaly.anomaly_type == "unusual_pattern":
            self.active_countermeasures.add("enhanced_validation")
        elif anomaly.anomaly_type == "invalid_parameters":
            self.active_countermeasures.add("parameter_lockdown")