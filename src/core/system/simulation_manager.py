from typing import Dict, Type, Optional
from ..interfaces.simulation_plugin import SimulationPlugin
from ..events.event_manager import EventManager
from .plugin_manager import PluginManager

class SimulationManager:
    def __init__(self, event_manager: EventManager, plugin_manager: PluginManager):
        self.event_manager = event_manager
        self.plugin_manager = plugin_manager
        self.active_simulations: Dict[str, SimulationPlugin] = {}
        self.hil_interfaces = {}
        
    async def load_simulation_plugin(self, module_path: str, class_name: str) -> None:
        plugin_class = self.plugin_manager.load_plugin(module_path, class_name)
        if not issubclass(plugin_class, SimulationPlugin):
            raise TypeError(f"Plugin {class_name} must inherit from SimulationPlugin")
        
        plugin = plugin_class(f"sim_{class_name}", self.event_manager)
        self.active_simulations[class_name] = plugin
        await plugin.initialize()
        
    async def run_simulation(self, sim_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if sim_type not in self.active_simulations:
            raise ValueError(f"Simulation type {sim_type} not loaded")
            
        simulator = self.active_simulations[sim_type]
        if not await simulator.validate_parameters(parameters):
            raise ValueError(f"Invalid parameters for simulation {sim_type}")
            
        return await simulator.run_simulation(parameters)
        
    async def register_hil_interface(self, interface_type: str, interface) -> None:
        """Register a HIL interface"""
        self.hil_interfaces[interface_type] = interface
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.HIL_INTERFACE_REGISTERED,
            component_id="simulation_manager",
            data={"interface_type": interface_type}
        ))

    async def run_hil_simulation(self, interface_type: str) -> Dict[str, Any]:
        """Run simulation with HIL interface"""
        if interface_type not in self.hil_interfaces:
            raise ValueError(f"HIL interface {interface_type} not registered")
            
        interface = self.hil_interfaces[interface_type]
        if not interface.connected:
            await interface.connect()
            
        return await interface.run_simulation()