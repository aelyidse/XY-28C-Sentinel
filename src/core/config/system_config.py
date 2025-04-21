from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

class SystemMode(Enum):
    STANDBY = "standby"
    MISSION = "mission"
    COMBAT = "combat"
    EMERGENCY = "emergency"

@dataclass
class SystemConfig:
    mode: SystemMode
    sensor_update_rate: float  # Hz
    navigation_update_rate: float  # Hz
    ai_processing_rate: float  # Hz
    communication_encryption_level: int
    max_autonomous_decision_time: float  # seconds
    emergency_protocol_timeout: float  # seconds
    emergency_response_timeout: float  # seconds

    @classmethod
    def default_config(cls) -> 'SystemConfig':
        return cls(
            mode=SystemMode.STANDBY,
            sensor_update_rate=100.0,
            navigation_update_rate=50.0,
            ai_processing_rate=25.0,
            communication_encryption_level=4,
            max_autonomous_decision_time=0.5,
            emergency_protocol_timeout=2.0,
            emergency_response_timeout=5.0
        )