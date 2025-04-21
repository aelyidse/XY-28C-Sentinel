from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from .environment import AtmosphericProperties, TerrainProperties
from .electronic_vulnerability import ElectronicSystem

@dataclass
class WeatherConditions:
    precipitation_rate: float  # mm/hr
    wind_velocity: np.ndarray  # m/s [u, v, w]
    cloud_coverage: float  # 0-1
    visibility: float  # m
    turbulence_intensity: float  # m²/s³

@dataclass
class UnifiedEnvironment:
    atmosphere: AtmosphericProperties
    terrain: TerrainProperties
    weather: WeatherConditions
    electronic_systems: List[ElectronicSystem]
    em_background: Dict[str, np.ndarray]  # Background EM noise
    obstacles: List[Dict[str, Any]]  # List of obstacle properties

class MultiDomainEnvironment:
    def __init__(self):
        self.c0 = 299792458  # Speed of light
        self.g0 = 9.81  # Gravitational acceleration
        self.R = 287.05  # Gas constant for air
        
    def compute_propagation_conditions(
        self,
        environment: UnifiedEnvironment,
        frequency: float
    ) -> Dict[str, np.ndarray]:
        # Compute atmospheric effects
        atmos_effects = self._compute_atmospheric_effects(
            environment.atmosphere,
            environment.weather,
            frequency
        )
        
        # Compute terrain and obstacle effects
        surface_effects = self._compute_surface_effects(
            environment.terrain,
            environment.obstacles
        )
        
        # Combine all environmental effects
        return {
            'refraction_index': atmos_effects['refraction_index'],
            'attenuation_factor': atmos_effects['attenuation'],
            'scattering_coefficient': surface_effects['scattering'],
            'reflection_coefficient': surface_effects['reflection'],
            'diffraction_paths': surface_effects['diffraction']
        }
        
    def _compute_atmospheric_effects(
        self,
        atmosphere: AtmosphericProperties,
        weather: WeatherConditions,
        frequency: float,
        altitude: float
    ) -> Dict[str, np.ndarray]:
        """Compute atmospheric effects with altitude-dependent models"""
        layer_props = atmosphere.get_layer_properties(altitude)
        
        if layer_props["layer"] == "troposphere":
            return self._compute_tropospheric_effects(layer_props, weather, frequency)
        elif layer_props["layer"] == "stratosphere":
            return self._compute_stratospheric_effects(layer_props, weather, frequency)
        # Calculate complex refractive index
        n = self._compute_refractive_index(atmosphere, frequency)
        
        # Calculate weather-dependent attenuation
        rain_attenuation = self._compute_rain_attenuation(
            weather.precipitation_rate,
            frequency
        )
        
        # Calculate atmospheric absorption
        molecular_absorption = self._compute_molecular_absorption(
            atmosphere.temperature,
            atmosphere.pressure,
            atmosphere.humidity,
            frequency
        )
        
        return {
            'refraction_index': n,
            'attenuation': rain_attenuation + molecular_absorption
        }
        
    def _compute_tropospheric_effects(
        self,
        layer_props: Dict[str, Any],
        weather: WeatherConditions,
        frequency: float
    ) -> Dict[str, np.ndarray]:
        """Troposphere-specific effects (weather, turbulence, etc.)"""
        # Calculate refractive index with water vapor effects
        e = layer_props["pressure"] * weather.humidity / 100
        n = 1 + (77.6/layer_props["temperature"]) * (
            layer_props["pressure"] + 4810 * e / layer_props["temperature"]
        ) * 1e-6
        
        # Calculate attenuation from rain and oxygen
        rain_atten = self._compute_rain_attenuation(weather.precipitation_rate, frequency)
        oxygen_atten = self._compute_oxygen_absorption(layer_props["temperature"], frequency)
        
        return {
            "refraction_index": n,
            "attenuation": rain_atten + oxygen_atten,
            "turbulence": weather.turbulence_intensity
        }
        
    def _compute_surface_effects(
        self,
        terrain: TerrainProperties,
        obstacles: List[Dict[str, Any]]
    ) -> Dict[str, np.ndarray]:
        # Calculate terrain reflection and scattering
        reflection = self._compute_surface_reflection(terrain)
        scattering = self._compute_surface_scattering(
            terrain.roughness,
            terrain.conductivity
        )
        
        # Calculate obstacle diffraction paths
        diffraction = self._compute_obstacle_diffraction(
            terrain.elevation,
            obstacles
        )
        
        return {
            'reflection': reflection,
            'scattering': scattering,
            'diffraction': diffraction
        }