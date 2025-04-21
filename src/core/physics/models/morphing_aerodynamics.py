from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from scipy.interpolate import CubicSpline
from ..models.biomimetic_actuators import BiomimeticActuatorArray

@dataclass
class MorphingSurface:
    actuator_arrays: Dict[str, BiomimeticActuatorArray]
    base_geometry: Dict[str, np.ndarray]
    material_properties: Dict[str, float]
    
    def calculate_aerodynamic_properties(
        self,
        control_voltages: Dict[str, np.ndarray],
        flow_conditions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate aerodynamic properties for current surface shape"""
        # Calculate surface deformation
        deformations = {
            name: array.simulate_deformation(voltages)
            for name, array in self.actuator_arrays.items()
        }
        
        # Calculate new surface geometry
        surface = self._calculate_surface_geometry(deformations)
        
        # Calculate aerodynamic coefficients
        return {
            **self._calculate_coefficients(surface, flow_conditions),
            'surface_profile': surface,
            'deformations': deformations
        }
        
    def _calculate_surface_geometry(
        self,
        deformations: Dict[str, Dict[str, np.ndarray]]
    ) -> Dict[str, np.ndarray]:
        """Combine actuator deformations into continuous surface"""
        # Interpolate between actuator arrays
        x = np.linspace(0, 1, 100)
        y = np.zeros_like(x)
        z = np.zeros_like(x)
        
        for name, deformation in deformations.items():
            profile = deformation['surface_profile']
            pos = self.actuator_arrays[name].positions
            y += CubicSpline(pos, profile[:,0])(x)
            z += CubicSpline(pos, profile[:,1])(x)
            
        return {
            'x': x * self.base_geometry['chord'],
            'y': y,
            'z': z
        }
        
    def _calculate_coefficients(
        self,
        surface: Dict[str, np.ndarray],
        flow: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate aerodynamic coefficients using thin airfoil theory"""
        # Calculate camber line
        dz_dx = np.gradient(surface['z'], surface['x'])
        theta = np.arctan(dz_dx)
        
        # Lift coefficient (simplified)
        cl = 2 * np.pi * (flow['angle_of_attack'] + np.mean(theta))
        
        # Moment coefficient
        cm = -0.25 * cl
        
        # Drag coefficient (profile drag + induced)
        cd = 0.02 + cl**2 / (np.pi * flow['aspect_ratio'] * 0.9)
        
        return {
            'lift_coefficient': cl,
            'drag_coefficient': cd,
            'moment_coefficient': cm,
            'efficiency': cl/cd
        }