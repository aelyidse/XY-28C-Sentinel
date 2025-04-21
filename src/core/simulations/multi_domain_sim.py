from typing import Dict, Any, List
from ..interfaces.simulation_plugin import SimulationPlugin
from ..physics.models.unified_environment import MultiDomainEnvironment, UnifiedEnvironment
from ..physics.models.electronic_vulnerability import EMPVulnerabilityAnalyzer
from ..physics.models.electromagnetics import EMPropagationModel

class MultiDomainSimulation(SimulationPlugin):
    async def initialize(self) -> None:
        self._state = {
            "simulation_type": "multi_domain",
            "capabilities": [
                "atmospheric_propagation",
                "terrain_interaction",
                "emp_effects",
                "system_vulnerability",
                "weather_impact"
            ]
        }
        self.environment = MultiDomainEnvironment()
        self.emp_model = EMPropagationModel()
        self.vulnerability_analyzer = EMPVulnerabilityAnalyzer()
        
    async def run_simulation(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Create unified environment
        env = self._create_environment(parameters['environment'])
        
        # Compute propagation conditions
        prop_conditions = self.environment.compute_propagation_conditions(
            env,
            parameters['operating_frequency']
        )
        
        # Compute EMP propagation
        emp_effects = await self.emp_model.compute_multi_source_propagation(
            parameters['emp_sources'],
            parameters['geometry'],
            parameters['material_properties'],
            {
                'atmosphere': env.atmosphere,
                'terrain': env.terrain,
                'weather': env.weather
            }
        )
        
        # Analyze system vulnerabilities
        system_effects = {}
        for system in env.electronic_systems:
            system_effects[system.system_type.value] = \
                self.vulnerability_analyzer.compute_system_damage(
                    system,
                    emp_effects['final_field'],
                    parameters['exposure_time']
                )
        
        return {
            'propagation_conditions': prop_conditions,
            'emp_effects': emp_effects,
            'system_effects': system_effects,
            'environmental_state': self._get_environment_state(env)
        }
        
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = {
            "environment",
            "operating_frequency",
            "emp_sources",
            "geometry",
            "material_properties",
            "exposure_time"
        }
        return all(param in parameters for param in required)