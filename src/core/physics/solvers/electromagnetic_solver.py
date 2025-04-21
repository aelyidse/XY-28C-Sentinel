import numpy as np
from typing import Dict, Any
from ..models.electromagnetics import EMPropagationModel, FieldInteractionModel

class ElectromagneticSolver:
    def __init__(self):
        self.propagation_model = EMPropagationModel()
        self.interaction_model = FieldInteractionModel()
        
    async def solve(self, params: Dict[str, Any]) -> Dict[str, np.ndarray]:
        # Solve Maxwell's equations for EMP propagation
        field_solution = await self.propagation_model.compute_field_propagation(
            params['source_strength'],
            params['geometry'],
            params['material_properties']
        )
        
        interaction_solution = await self.interaction_model.compute_field_interactions(
            field_solution,
            params['target_properties']
        )
        
        return {
            'electric_field': interaction_solution['e_field'],
            'magnetic_field': interaction_solution['b_field'],
            'induced_currents': interaction_solution['currents']
        }