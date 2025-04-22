from typing import Dict, List, Any
from dataclasses import dataclass
import numpy as np

@dataclass
class BiomimeticMaterial:
    name: str
    base_properties: Dict[str, float]
    adaptation_mechanisms: List[str]
    environmental_response: Dict[str, Any]
    fabrication_parameters: Dict[str, Any]

class BiomimeticMaterialLibrary:
    def __init__(self):
        self.materials = {}
        self.adaptation_mechanisms = {}
        
    def register_material(
        self,
        material: BiomimeticMaterial
    ) -> None:
        """Register a new biomimetic material"""
        self.materials[material.name] = material
        
    def find_suitable_materials(
        self,
        requirements: Dict[str, Any]
    ) -> List[BiomimeticMaterial]:
        """Find materials matching given requirements"""
        suitable = []
        for material in self.materials.values():
            if self._check_material_suitability(material, requirements):
                suitable.append(material)
        return suitable
        
    def _check_material_suitability(
        self,
        material: BiomimeticMaterial,
        requirements: Dict[str, Any]
    ) -> bool:
        """Check if material meets requirements"""
        for prop, value in requirements.items():
            if prop in material.base_properties:
                if not self._is_property_suitable(
                    material.base_properties[prop],
                    value
                ):
                    return False
        return True