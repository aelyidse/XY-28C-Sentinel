from dataclasses import dataclass
from enum import Enum
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.constants import h, k, mu_0, hbar

class QuantumSensorType(Enum):
    SQUID = "squid"
    NV_CENTER = "nv_center"

@dataclass
class SQUIDParameters:
    junction_critical_current: float  # A
    loop_area: float  # m²
    inductance: float  # H
    operating_temperature: float  # K
    noise_temperature: float  # K
    shunt_resistance: float  # Ω

@dataclass
class NVCenterParameters:
    zero_field_splitting: float  # Hz (D ≈ 2.87 GHz)
    gyromagnetic_ratio: float  # Hz/T (γ ≈ 28 GHz/T)
    coherence_time: float  # s
    laser_power: float  # W
    microwave_frequency: float  # Hz
    center_density: float  # m⁻³

class QuantumMagneticSensor:
    def __init__(
        self,
        sensor_type: QuantumSensorType,
        parameters: Union[SQUIDParameters, NVCenterParameters]
    ):
        self.sensor_type = sensor_type
        self.parameters = parameters
        self.temperature = parameters.operating_temperature
        self.sampling_rate = 1e4  # Hz
        
    def measure_magnetic_field(
        self,
        ambient_field: np.ndarray,
        integration_time: float
    ) -> Tuple[np.ndarray, float]:
        if self.sensor_type == QuantumSensorType.SQUID:
            return self._squid_measurement(ambient_field, integration_time)
        else:
            return self._nv_center_measurement(ambient_field, integration_time)
            
    def _squid_measurement(
        self,
        field: np.ndarray,
        integration_time: float
    ) -> Tuple[np.ndarray, float]:
        params = self.parameters
        
        # Calculate flux through SQUID loop
        flux = field * params.loop_area
        
        # Phase difference across junction
        phase = 2 * np.pi * flux / (h / (2 * params.junction_critical_current))
        
        # Calculate SQUID response with thermal noise
        thermal_noise = self._calculate_squid_noise(integration_time)
        
        # Compute measured field with noise
        measured_field = field + thermal_noise
        
        # Calculate sensitivity
        sensitivity = self._calculate_squid_sensitivity()
        
        return measured_field, sensitivity
        
    def _nv_center_measurement(
        self,
        field: np.ndarray,
        integration_time: float
    ) -> Tuple[np.ndarray, float]:
        params = self.parameters
        
        # Calculate Zeeman splitting
        zeeman_shift = params.gyromagnetic_ratio * np.linalg.norm(field)
        
        # Calculate resonance frequencies
        resonances = self._calculate_nv_resonances(field)
        
        # Simulate optical readout with shot noise
        readout_signal = self._simulate_nv_readout(resonances, integration_time)
        
        # Calculate measurement uncertainty
        uncertainty = self._calculate_nv_uncertainty(integration_time)
        
        # Reconstruct magnetic field vector
        measured_field = self._reconstruct_field_vector(readout_signal)
        
        return measured_field, uncertainty
        
    def _calculate_squid_noise(self, integration_time: float) -> float:
        params = self.parameters
        
        # Thermal noise in SQUID
        thermal_noise = np.sqrt(4 * k * params.noise_temperature * 
                              params.shunt_resistance / integration_time)
        
        # Flux noise
        flux_noise = thermal_noise * params.inductance
        
        return flux_noise / (params.loop_area * mu_0)
        
    def _calculate_squid_sensitivity(self) -> float:
        params = self.parameters
        
        # Energy sensitivity
        energy_sensitivity = 2 * k * params.noise_temperature * params.inductance
        
        # Field sensitivity
        return np.sqrt(energy_sensitivity) / (params.loop_area * mu_0)
        
    def _calculate_nv_resonances(
        self,
        field: np.ndarray
    ) -> np.ndarray:
        params = self.parameters
        
        # Zero-field splitting
        D = params.zero_field_splitting
        
        # Magnetic field magnitude
        B_mag = np.linalg.norm(field)
        
        # Calculate resonance frequencies for all NV orientations
        resonances = np.zeros(4)  # 4 possible NV orientations
        for i, theta in enumerate([54.7, 54.7, 54.7, 54.7]):  # tetrahedral angles
            # Resonance frequency including zero-field splitting and Zeeman effect
            resonances[i] = D + params.gyromagnetic_ratio * B_mag * np.cos(np.deg2rad(theta))
            
        return resonances
        
    def _simulate_nv_readout(
        self,
        resonances: np.ndarray,
        integration_time: float
    ) -> np.ndarray:
        params = self.parameters
        
        # Simulate photoluminescence
        base_signal = params.laser_power * integration_time
        
        # Add shot noise
        shot_noise = np.random.poisson(base_signal, size=len(resonances))
        
        # Calculate contrast based on resonance detuning
        contrast = self._calculate_nv_contrast(resonances)
        
        return base_signal * contrast + shot_noise
        
    def _calculate_nv_contrast(
        self,
        resonances: np.ndarray
    ) -> np.ndarray:
        params = self.parameters
        
        # Calculate detuning from microwave drive
        detuning = resonances - params.microwave_frequency
        
        # Lorentzian lineshape
        gamma = 1 / params.coherence_time
        contrast = 1 / (1 + (2 * detuning / gamma)**2)
        
        return contrast