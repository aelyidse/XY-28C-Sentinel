from abc import ABC, abstractmethod
from typing import Dict, List
import numpy as np
from ..events.event_manager import EventManager

class FaultDetector(ABC):
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.fault_history = []
        self.detection_thresholds = {}
        
    @abstractmethod
    async def detect_faults(self, sensor_data: Dict) -> List[Dict]:
        """Detect faults in hardware components"""
        pass
        
    @abstractmethod
    async def diagnose_fault(self, fault_data: Dict) -> Dict:
        """Diagnose detected faults"""
        pass
        
    async def log_fault(self, fault: Dict) -> None:
        """Log detected fault"""
        self.fault_history.append(fault)
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.HARDWARE_FAULT_DETECTED,
            component_id="fault_detector",
            data=fault
        ))
        
    def _calculate_health_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall health score from component metrics"""
        weights = {
            'vibration': 0.3,
            'temperature': 0.25,
            'voltage': 0.2,
            'current': 0.15,
            'signal_noise': 0.1
        }
        return sum(metrics[k] * weights[k] for k in weights)