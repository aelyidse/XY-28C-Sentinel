from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np

@dataclass
class ElectroactivePolymerProperties:
    dielectric_constant: float
    elastic_modulus: float  # MPa
    max_strain: float  # %
    thickness: float  # μm
    electrode_resistance: float  # Ω/cm²
    response_time: float  # ms

class ElectroactivePolymerActuator:
    def __init__(self, properties: ElectroactivePolymerProperties):
        self.properties = properties
        self.epsilon_0 = 8.854e-12  # F/m
        
    def calculate_displacement(
        self,
        voltage: float,
        frequency: float = 0.0
    ) -> Dict[str, float]:
        """Calculate actuator displacement under applied voltage"""
        # Calculate Maxwell stress
        stress = self._calculate_maxwell_stress(voltage)
        
        # Calculate strain (simplified linear model)
        strain = min(
            stress / self.properties.elastic_modulus * 1e6,
            self.properties.max_strain / 100
        )
        
        # Calculate frequency-dependent response
        if frequency > 0:
            strain *= self._frequency_response(frequency)
            
        return {
            'displacement': strain * self.properties.thickness * 1e-6,  # meters
            'strain': strain * 100,  # percentage
            'force': stress * self.properties.thickness * 1e-6,  # N
            'response_time': self._calculate_response_time(voltage, frequency)
        }
        
    def _calculate_maxwell_stress(self, voltage: float) -> float:
        """Calculate Maxwell stress in the polymer"""
        return 0.5 * self.properties.dielectric_constant * self.epsilon_0 * \
               (voltage / (self.properties.thickness * 1e-6))**2  # Pa
               
    def _frequency_response(self, frequency: float) -> float:
        """Calculate frequency-dependent response factor"""
        tau = self.properties.response_time * 1e-3  # Convert to seconds
        return 1 / np.sqrt(1 + (2 * np.pi * frequency * tau)**2)
        
    def _calculate_response_time(self, voltage: float, frequency: float) -> float:
        """Calculate effective response time"""
        rc_time = self.properties.electrode_resistance * \
                 (self.properties.dielectric_constant * self.epsilon_0) * \
                 (self.properties.thickness * 1e-6)  # seconds
        return np.sqrt(rc_time**2 + (1/(2 * np.pi * frequency))**2) if frequency > 0 else rc_time