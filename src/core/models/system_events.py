from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from ..events.event_manager import Event

class SystemEventType(Enum):
    COMBAT_READY = "combat_ready"
    TARGET_ACQUIRED = "target_acquired"
    THREAT_DETECTED = "threat_detected"
    SYSTEM_STATUS_CHANGED = "system_status_changed"
    NAVIGATION_UPDATE = "navigation_update"
    SENSOR_DATA = "sensor_data"
    STEALTH_STATUS = "stealth_status"
    POWER_WARNING = "power_warning"
    MISSION_UPDATE = "mission_update"
    EMERGENCY_CONDITION = "emergency_condition"

@dataclass
class SystemEvent(Event):
    event_type: SystemEventType
    component_id: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: int
    source_id: str