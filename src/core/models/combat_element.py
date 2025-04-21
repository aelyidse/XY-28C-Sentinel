from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class CombatElementType(Enum):
    IMPLOSIVE_GENERATOR = "implosive_generator"
    CLUSTER_MUNITION = "cluster_munition"

@dataclass
class ExplosiveMagneticGenerator:
    frequency_range: tuple[float, float]  # Hz
    pulse_strength: float  # V/m
    detonation_delay: float  # seconds
    charge_weight: float  # kg
    
@dataclass
class CombatElement:
    element_type: CombatElementType
    generators: List[ExplosiveMagneticGenerator]
    ejection_charge: Optional[float] = None  # kg
    housing_thickness: float  # mm
    thermal_protection_rating: float  # K
    deployment_ready: bool = False