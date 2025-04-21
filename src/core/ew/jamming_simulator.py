from enum import Enum, auto
import numpy as np
from typing import Dict, List
from ..events.event_manager import EventManager

class JammingType(Enum):
    NOISE = auto()
    SPOT = auto()
    SWEEP = auto()
    PULSE = auto()

class JammingSimulator:
    def __init__(self, em_sensor: EMSensor, event_manager: EventManager):
        self.em_sensor = em_sensor
        self.event_manager = event_manager
        self.active_jammers: Dict[str, Dict] = {}
        
    async def simulate_jamming_attack(self, jammer_id: str, params: Dict) -> None:
        """Simulate a jamming attack with given parameters"""
        jam_type = JammingType[params['type'].upper()]
        
        if jam_type == JammingType.NOISE:
            await self._simulate_noise_jamming(params)
        elif jam_type == JammingType.SPOT:
            await self._simulate_spot_jamming(params)
        elif jam_type == JammingType.SWEEP:
            await self._simulate_sweep_jamming(params)
            
        self.active_jammers[jammer_id] = params
        await self._notify_jamming_start(jammer_id, params)
        
    async def _simulate_noise_jamming(self, params: Dict) -> None:
        """Simulate broadband noise jamming"""
        self.em_sensor.jamming_effects['noise_floor'] = params.get('noise_floor', -70)
        
    async def _simulate_spot_jamming(self, params: Dict) -> None:
        """Simulate spot frequency jamming"""
        self.em_sensor.add_jammer(
            params['frequency'],
            params.get('bandwidth', 1e6),
            params.get('power', 30)
        )
        
    async def _simulate_sweep_jamming(self, params: Dict) -> None:
        """Simulate sweeping jamming signal"""
        # This would be implemented with a background task that moves the jamming frequency
        pass
        
    async def _notify_jamming_start(self, jammer_id: str, params: Dict) -> None:
        """Notify systems about jamming attack"""
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.JAMMING_DETECTED,
            component_id="jamming_simulator",
            data={
                "jammer_id": jammer_id,
                "params": params,
                "timestamp": datetime.now()
            },
            priority=1
        ))