import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class MaterialRecord:
    name: str
    category: str
    properties: Dict[str, float]
    cost: float
    environmental_impact: Dict[str, float]

class MaterialDatabase:
    def __init__(self):
        self.materials = self._load_materials()
        
    def _load_materials(self) -> Dict[str, MaterialRecord]:
        return {
            'carbon_fiber': MaterialRecord(
                name='carbon_fiber',
                category='composite',
                properties={
                    'stiffness': 230e9,
                    'strength': 3.5e9,
                    'density': 1.75e3,
                    'thermal_conductivity': 8.0
                },
                cost=120.0,
                environmental_impact={'co2': 25.0, 'energy': 180.0}
            ),
            # ... other materials
        }
        
    def query_materials(self, filters: Dict[str, Any]) -> List[MaterialRecord]:
        """Query materials based on property filters"""
        results = []
        for mat in self.materials.values():
            match = True
            for prop, (min_val, max_val) in filters.items():
                if prop in mat.properties:
                    if not (min_val <= mat.properties[prop] <= max_val):
                        match = False
                        break
            if match:
                results.append(mat)
        return results