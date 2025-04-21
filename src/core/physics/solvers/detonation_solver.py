import numpy as np
from typing import Dict, Any
from ..models.explosions import DetonationModel, ShockwaveModel

class DetonationSolver:
    def __init__(self):
        self.detonation_model = DetonationModel()
        self.shockwave_model = ShockwaveModel()
        
    async def solve(self, params: Dict[str, Any]) -> Dict[str, np.ndarray]:
        # Solve explosion dynamics
        detonation_solution = await self.detonation_model.compute_detonation(
            params['charge_mass'],
            params['detonation_velocity'],
            params['geometry']
        )
        
        shockwave_solution = await self.shockwave_model.compute_shockwave_propagation(
            detonation_solution,
            params['ambient_conditions']
        )
        
        return {
            'pressure_field': shockwave_solution['pressure'],
            'temperature_field': shockwave_solution['temperature'],
            'velocity_field': shockwave_solution['velocity']
        }