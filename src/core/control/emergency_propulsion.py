from enum import Enum, auto
from dataclasses import dataclass
import numpy as np

class EmergencyMode(Enum):
    ENGINE_FAILURE = auto()
    COOLING_FAILURE = auto()
    MHD_FAILURE = auto()
    THRUST_VECTOR_FAILURE = auto()

@dataclass
class EmergencyProtocol:
    max_throttle: float
    cooling_rate: float
    mhd_voltage: float
    vector_deflection: tuple[float, float]

class EmergencyPropulsionController:
    def __init__(self, propulsion_system):
        self.propulsion = propulsion_system
        self.protocols = {
            EmergencyMode.ENGINE_FAILURE: EmergencyProtocol(
                max_throttle=0.5,
                cooling_rate=1.0,
                mhd_voltage=3000,
                vector_deflection=(0, 0)
            ),
            EmergencyMode.COOLING_FAILURE: EmergencyProtocol(
                max_throttle=0.3,
                cooling_rate=0.0,
                mhd_voltage=1000,
                vector_deflection=(0, 0)
            ),
            EmergencyMode.MHD_FAILURE: EmergencyProtocol(
                max_throttle=0.7,
                cooling_rate=0.5,
                mhd_voltage=0,
                vector_deflection=(0, 0)
            ),
            EmergencyMode.THRUST_VECTOR_FAILURE: EmergencyProtocol(
                max_throttle=0.6,
                cooling_rate=0.8,
                mhd_voltage=2000,
                vector_deflection=(0, 0)
            )
        }

    async def activate_emergency_mode(self, failure_type: EmergencyMode) -> None:
        """Activate emergency propulsion protocol"""
        protocol = self.protocols[failure_type]
        
        # Apply emergency settings
        await self.propulsion.set_throttle(protocol.max_throttle)
        
        if hasattr(self.propulsion, 'cooling_system'):
            await self.propulsion.cooling_system.set_cooling_rate(protocol.cooling_rate)
            
        if hasattr(self.propulsion, 'mhd_accelerator'):
            await self.propulsion.configure_mhd_voltage(protocol.mhd_voltage)
            
        if hasattr(self.propulsion, 'thrust_vectoring'):
            await self.propulsion.set_thrust_vector(*protocol.vector_deflection)