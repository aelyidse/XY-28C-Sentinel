from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from enum import Enum

class ElectronicSignatureType(Enum):
    RADAR_SYSTEM = "radar_system"
    COMMUNICATION_ARRAY = "communication_array"
    COMMAND_CENTER = "command_center"
    EW_SYSTEM = "electronic_warfare_system"
    POWER_INFRASTRUCTURE = "power_infrastructure"
    COMPUTING_FACILITY = "computing_facility"

@dataclass
class SpectralSignature:
    type: ElectronicSignatureType
    thermal_profile: np.ndarray  # Temperature distribution (K)
    em_emissions: np.ndarray  # EM emission spectrum (W/m²/nm)
    rf_signature: np.ndarray  # RF emission pattern (dBm)
    spatial_pattern: np.ndarray  # Spatial distribution
    confidence_threshold: float  # Match confidence threshold

class SpectralDatabase:
    def __init__(self):
        self.signatures: Dict[str, SpectralSignature] = {}
        self.wavelength_bands = {
            'visible': (380, 750),  # nm
            'nir': (750, 1400),    # nm
            'swir': (1400, 3000),  # nm
            'thermal': (8000, 12000)  # nm
        }
        
    def add_signature(
        self,
        signature_id: str,
        signature: SpectralSignature
    ) -> None:
        self.signatures[signature_id] = signature
        
    def get_signature(
        self,
        signature_id: str
    ) -> Optional[SpectralSignature]:
        return self.signatures.get(signature_id)