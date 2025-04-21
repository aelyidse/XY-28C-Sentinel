from abc import abstractmethod
from typing import Dict, Any
from .system_component import SystemComponent

class SimulationPlugin(SystemComponent):
    @abstractmethod
    async def run_simulation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def get_simulation_capabilities(self) -> Dict[str, Any]:
        pass