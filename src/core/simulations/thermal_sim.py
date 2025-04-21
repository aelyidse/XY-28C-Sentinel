from typing import Dict, Any
from ..interfaces.simulation_plugin import SimulationPlugin
from ..physics.models.thermal import ThermalSimulation, ThermalProperties

class ThermalSimulationPlugin(SimulationPlugin):
    async def initialize(self) -> None:
        self._state = {
            "simulation_type": "thermal",
            "capabilities": [
                "environmental_thermal",
                "material_response", 
                "transient_analysis",
                "hypersonic_heating"  # New capability
            ]
        }
        
    async def run_simulation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if 'mach' in parameters:  # Hypersonic mode
            thermal_model = HypersonicThermalSimulation(parameters['environment'])
            results = await thermal_model.simulate_hypersonic_thermal(
                material=parameters['material'],
                geometry=parameters['geometry'],
                flight_conditions=parameters,
                duration=parameters['duration'],
                time_step=parameters.get('time_step', 1.0)
            )
        else:  # Standard mode
            thermal_model = ThermalSimulation(parameters['environment'])
            results = await thermal_model.simulate_thermal_behavior(
                material=parameters['material'],
                geometry=parameters['geometry'],
                heat_sources=parameters.get('heat_sources', {}),
                duration=parameters['duration'],
                time_step=parameters.get('time_step', 1.0)
            )
            
        return {
            **results,
            'stability_analysis': self._analyze_stability(results)
        }
        
    def _analyze_stability(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze thermal stability characteristics"""
        temp_history = results['temperature_history']
        time_points = results['time_points']
        
        # Calculate rate of temperature change
        temp_gradient = np.gradient(temp_history, time_points, axis=0)
        
        return {
            'max_gradient': np.max(np.abs(temp_gradient)),
            'equilibrium_time': self._find_equilibrium_time(temp_history),
            'hot_spots': self._find_hot_spots(temp_history)
        }
        
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = {
            "environment",
            "material",
            "geometry",
            "duration"
        }
        return all(param in parameters for param in required)