import numpy as np

class PhaseShifterArray:
    def calculate_phase_shifts(
        self,
        steering_angle: Tuple[float, float],
        array_position: np.ndarray,
        focal_distance: float
    ) -> np.ndarray:
        """Calculate phase shifts for beam steering and focusing"""
        az, el = steering_angle
        k = 2 * np.pi * focal_distance
        
        # Calculate phase delays for each element
        phase_shifts = k * (
            np.sin(az) * np.cos(el) * array_position[0] +
            np.sin(el) * array_position[1] +
            (np.cos(az) * np.cos(el) - 1) * array_position[2]
        )
        
        return phase_shifts
        
    def apply_metamaterial_correction(
        self,
        phase_shifts: np.ndarray,
        metamaterial: MetamaterialProperties
    ) -> np.ndarray:
        """Adjust phase shifts for metamaterial dispersion"""
        # Compensate for frequency-dependent phase shifts
        return phase_shifts * metamaterial.focusing_gain