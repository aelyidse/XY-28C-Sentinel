from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np
from ..interfaces.sensor_plugin import SensorPlugin
from ..interfaces.simulation_plugin import SimulationPlugin

class SensorSimulationInterface(SensorPlugin, SimulationPlugin):
    """Base interface for sensor simulation"""
    
    @abstractmethod
    async def set_simulation_parameters(self, params: Dict[str, Any]) -> bool:
        """Set simulation parameters"""
        pass
    
    @abstractmethod
    async def get_simulation_state(self) -> Dict[str, Any]:
        """Get current simulation state"""
        pass
    
    @abstractmethod
    async def step_simulation(self, delta_time: float) -> Dict[str, Any]:
        """Advance simulation by specified time step"""
        pass