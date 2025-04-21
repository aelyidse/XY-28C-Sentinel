import numpy as np
from typing import Dict, List
from .electroactive_polymers import ElectroactivePolymerActuator

class BiomimeticActuatorArray:
    def __init__(self, positions: np.ndarray, material_properties: Dict[str, float]):
        self.positions = positions
        self.material = material_properties
        
    def simulate_deformation(
        self,
        control_voltages: np.ndarray,
        frequency: float = 0.0
    ) -> Dict[str, Any]:
        """Simulate actuator array deformation under control voltages"""
        displacements = []
        forces = []
        
        for voltage in control_voltages:
            # Calculate piezoelectric displacement
            displacement = voltage * self.material['piezo_coefficient']
            
            # Apply frequency-dependent damping
            if frequency > 0:
                displacement *= self._frequency_response(frequency)
                
            displacements.append(displacement)
            forces.append(displacement * self.material['stiffness'])
            
        return {
            'displacements': np.array(displacements),
            'forces': np.array(forces),
            'power_consumption': np.sum(control_voltages**2) / self.material['resistance']
        }
        
    def _frequency_response(self, frequency: float) -> float:
        """Calculate frequency response damping factor"""
        natural_freq = self.material['natural_frequency']
        damping_ratio = self.material['damping_ratio']
        
        if frequency >= natural_freq:
            return 1 / ((frequency/natural_freq)**2)
        return 1.0
        
    def _calculate_surface_profile(self, displacements: List[float]) -> np.ndarray:
        """Calculate continuous surface profile from discrete actuators"""
        from scipy.interpolate import CubicSpline
        return CubicSpline(self.positions, displacements)(np.linspace(0, 1, 100))
        
    def _calculate_curvature(self, profile: np.ndarray) -> float:
        """Calculate average curvature of deformed surface"""
        dy = np.gradient(profile)
        d2y = np.gradient(dy)
        return np.mean(d2y / (1 + dy**2)**1.5)