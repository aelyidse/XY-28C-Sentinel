from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import numpy as np

class SensorType(Enum):
    LIDAR = "lidar"
    QUANTUM_MAGNETIC = "quantum_magnetic"
    HYPERSPECTRAL = "hyperspectral"
    RANGEFINDER = "rangefinder"
    VIDEO = "video"

@dataclass
class LiDARConfig:
    scan_rate: float  # Hz
    point_density: float  # points/m²
    max_range: float  # meters
    beam_divergence: float  # mrad
    
@dataclass
class QuantumSensorConfig:
    sensitivity: float  # Tesla
    sampling_rate: float  # Hz
    noise_floor: float  # Tesla/√Hz
    operating_temperature: float  # K

@dataclass
class HyperspectralConfig:
    spectral_bands: List[tuple[float, float]]  # wavelength ranges (nm)
    spatial_resolution: float  # pixels/degree
    frame_rate: float  # Hz
    integration_time: float  # ms

@dataclass
class SensorSystem:
    sensor_type: SensorType
    position: tuple[float, float, float]  # x, y, z coordinates
    orientation: tuple[float, float, float]  # roll, pitch, yaw
    field_of_view: tuple[float, float]  # horizontal, vertical (degrees)
    config: Dict  # Specific configuration for each sensor type
    calibration_matrix: Optional[np.ndarray] = None