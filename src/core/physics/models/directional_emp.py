import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List
from scipy.special import hankel1

@dataclass
class DirectionalEMPConfig:
    """Configuration for directional EMP focusing"""
    focal_distance: float  # meters
    beam_width: float  # radians
    steering_angle: Tuple[float, float]  # (azimuth, elevation) in radians
    polarization: str  # 'linear', 'circular'
    frequency_range: Tuple[float, float]  # Hz

class DirectionalEMPSimulator:
    def __init__(self, propagation_model: EMPropagationModel):
        self.propagation_model = propagation_model
        self.phase_shifters = PhaseShifterArray()
        
    async def simulate_focused_emp(
        self,
        source: Dict[str, Any],
        config: DirectionalEMPConfig,
        metamaterial: MetamaterialProperties,
        environment: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """Simulate directional EMP with metamaterial focusing"""
        # Calculate phase shifts for beam steering
        phase_shifts = self.phase_shifters.calculate_phase_shifts(
            config.steering_angle,
            source['position'],
            config.focal_distance
        )
        
        # Generate phased array effect
        phased_sources = self._create_phased_sources(
            source,
            phase_shifts,
            metamaterial.resonant_frequency
        )
        
        # Simulate propagation with metamaterial enhancement
        return await self.propagation_model.compute_multi_source_propagation(
            sources=phased_sources,
            geometry={
                'observation_grid': environment['observation_grid'],
                'time': environment['time']
            },
            material_properties=metamaterial,
            environment_properties=environment
        )
        
    def _create_phased_sources(
        self,
        base_source: Dict[str, Any],
        phase_shifts: np.ndarray,
        frequency: float
    ) -> List[Dict[str, Any]]:
        """Create virtual phased array sources"""
        sources = []
        for i, phase_shift in enumerate(phase_shifts):
            sources.append({
                'position': base_source['position'] + np.array([i*0.1, 0, 0]),  # 10cm spacing
                'phase': base_source['phase'] + phase_shift,
                'amplitude': base_source['amplitude'],
                'frequency': frequency,
                'delay': base_source['delay']
            })
        return sources