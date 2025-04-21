from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np
from scipy.special import hankel1

@dataclass
class EMPSource:
    position: np.ndarray  # [x, y, z] in meters
    phase: float  # radians
    amplitude: float  # V/m
    frequency: float  # Hz
    delay: float  # seconds

class InterferenceCalculator:
    def __init__(self):
        self.c0 = 299792458  # Speed of light in vacuum
        
    def compute_interference_pattern(
        self,
        sources: List[EMPSource],
        observation_grid: np.ndarray,
        time: float
    ) -> Dict[str, np.ndarray]:
        total_field = np.zeros_like(observation_grid[:,:,0], dtype=complex)
        
        for source in sources:
            # Calculate distance from source to each point
            distances = np.sqrt(np.sum((observation_grid - source.position) ** 2, axis=2))
            
            # Calculate phase including time delay
            k = 2 * np.pi * source.frequency / self.c0
            phase = k * distances - 2 * np.pi * source.frequency * (time - source.delay)
            
            # Calculate amplitude decay with distance (1/r dependence)
            amplitude = source.amplitude / distances
            
            # Add contribution from this source
            field_contribution = amplitude * np.exp(1j * (phase + source.phase))
            total_field += field_contribution
            
        return {
            'magnitude': np.abs(total_field),
            'phase': np.angle(total_field),
            'real': np.real(total_field),
            'imaginary': np.imag(total_field)
        }