from abc import abstractmethod
from typing import Dict, Any, List
from .system_component import SystemComponent
from .plugin import Plugin

class SimulationPlugin(SystemComponent, Plugin):
    @abstractmethod
    async def run_simulation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        pass
    
    def get_plugin_type(self) -> str:
        return "simulation"
    
    def get_capabilities(self) -> List[str]:
        return self._state.get("capabilities", [])
    
    async def get_simulation_capabilities(self) -> Dict[str, Any]:
        return self._state.get("capabilities", [])
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "type": "simulation",
            "simulation_type": self._state.get("simulation_type", "unknown"),
            "capabilities": self.get_capabilities()
        }