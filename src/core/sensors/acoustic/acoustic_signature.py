import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class AcousticProperties:
    frequency_range: tuple[float, float]  # Hz
    directivity_pattern: np.ndarray
    source_level: float  # dB
    harmonic_content: Dict[int, float]  # harmonic number: amplitude ratio

class AcousticSignaturePredictor:
    def __init__(self, environment: UnifiedEnvironment):
        self.environment = environment
        self.speed_of_sound = 343.0  # m/s at 20°C
        self.reference_pressure = 20e-6  # Pa
    
    def predict_signature(
        self,
        source_properties: AcousticProperties,
        position: np.ndarray,
        receiver_position: np.ndarray,
        velocity: np.ndarray = None
    ) -> Dict[str, np.ndarray]:
        """Predict acoustic signature at receiver position"""
        # Calculate propagation distance
        distance = np.linalg.norm(receiver_position - position)
        
        # Apply atmospheric absorption
        absorption = self._calculate_atmospheric_absorption(
            source_properties.frequency_range,
            distance
        )
        
        # Apply Doppler effect if velocity is provided
        if velocity is not None:
            freq_shift = self._calculate_doppler_shift(
                source_properties.frequency_range,
                velocity,
                receiver_position - position
            )
        else:
            freq_shift = source_properties.frequency_range
        
        # Calculate received sound pressure level
        spl = self._calculate_sound_pressure_level(
            source_properties.source_level,
            distance,
            absorption
        )
        
        # Generate harmonic spectrum
        spectrum = self._generate_harmonic_spectrum(
            freq_shift,
            source_properties.harmonic_content,
            spl
        )
        
        return {
            'frequency_range': freq_shift,
            'sound_pressure_level': spl,
            'spectrum': spectrum,
            'distance': distance,
            'directivity': self._apply_directivity(
                source_properties.directivity_pattern,
                position,
                receiver_position
            )
        }
    
    def _calculate_atmospheric_absorption(
        self,
        frequency_range: tuple[float, float],
        distance: float
    ) -> float:
        """Calculate atmospheric absorption in dB/m"""
        # Using ISO 9613-1 standard
        temp = self.environment.atmosphere.temperature
        humidity = self.environment.weather.humidity
        freq = np.mean(frequency_range)
        
        # Calculate absorption coefficient
        alpha = 1.84e-11 * (temp**0.5) * (freq**2) / (
            1 + 1.275e-5 * (freq * temp**-1.5)
        ) + 0.1068 * np.exp(-3352/temp) * (freq**2) / (
            (freq**2 + 1.101e5)**2 + humidity/100
        )
        
        return alpha * distance
    
    def _calculate_doppler_shift(
        self,
        frequency_range: tuple[float, float],
        velocity: np.ndarray,
        direction: np.ndarray
    ) -> tuple[float, float]:
        """Calculate Doppler shifted frequency range"""
        relative_velocity = np.dot(velocity, direction) / np.linalg.norm(direction)
        doppler_factor = self.speed_of_sound / (self.speed_of_sound - relative_velocity)
        return (
            frequency_range[0] * doppler_factor,
            frequency_range[1] * doppler_factor
        )
    
    def _calculate_sound_pressure_level(
        self,
        source_level: float,
        distance: float,
        absorption: float
    ) -> float:
        """Calculate received sound pressure level"""
        # Inverse square law + atmospheric absorption
        return source_level - 20 * np.log10(distance) - absorption
    
    def _generate_harmonic_spectrum(
        self,
        frequency_range: tuple[float, float],
        harmonic_content: Dict[int, float],
        base_spl: float
    ) -> Dict[int, float]:
        """Generate harmonic spectrum with amplitudes"""
        fundamental = np.mean(frequency_range)
        spectrum = {}
        
        for harmonic, ratio in harmonic_content.items():
            freq = fundamental * harmonic
            spectrum[freq] = base_spl + 20 * np.log10(ratio)
            
        return spectrum
    
    def _apply_directivity(
        self,
        pattern: np.ndarray,
        source_pos: np.ndarray,
        receiver_pos: np.ndarray
    ) -> float:
        """Apply directivity pattern to source-receiver geometry"""
        direction = receiver_pos - source_pos
        direction /= np.linalg.norm(direction)
        
        # Convert to spherical coordinates (theta, phi)
        theta = np.arccos(direction[2])
        phi = np.arctan2(direction[1], direction[0])
        
        # Interpolate directivity pattern (simplified)
        theta_idx = int(np.degrees(theta) % 360)
        phi_idx = int(np.degrees(phi) % 360)
        return pattern[theta_idx, phi_idx]