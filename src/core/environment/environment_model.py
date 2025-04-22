"""
Environment Modeling Module

This module provides environmental conditions modeling for the XY-28C-Sentinel system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import asyncio
from datetime import datetime, time

class WeatherCondition(Enum):
    """Weather condition types"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    SNOW = "snow"
    FOG = "fog"
    STORM = "storm"

class TimeOfDay(Enum):
    """Time of day periods"""
    DAWN = "dawn"
    DAY = "day"
    DUSK = "dusk"
    NIGHT = "night"

@dataclass
class AtmosphericConditions:
    """Atmospheric conditions data"""
    temperature: float = 20.0  # Celsius
    humidity: float = 0.5  # 0-1 scale
    pressure: float = 101.3  # kPa
    wind_speed: float = 0.0  # m/s
    wind_direction: float = 0.0  # degrees
    precipitation: float = 0.0  # mm/h
    visibility: float = 10000.0  # meters
    cloud_cover: float = 0.0  # 0-1 scale

class EnvironmentModel:
    """Environment model for XY-28C-Sentinel"""
    
    def __init__(self):
        """Initialize environment model"""
        self.weather = WeatherCondition.CLEAR
        self.time_of_day = TimeOfDay.DAY
        self.atmospheric = AtmosphericConditions()
        self.light_level = 1.0  # 0-1 scale
        self.em_interference = 0.0  # 0-1 scale
        
    async def update_weather(self, condition: WeatherCondition) -> None:
        """Update weather condition and related atmospheric properties"""
        self.weather = condition
        
        # Update atmospheric conditions based on weather
        if condition == WeatherCondition.CLEAR:
            self.atmospheric.cloud_cover = 0.1
            self.atmospheric.visibility = 10000.0
            self.atmospheric.precipitation = 0.0
            
        elif condition == WeatherCondition.CLOUDY:
            self.atmospheric.cloud_cover = 0.7
            self.atmospheric.visibility = 5000.0
            self.atmospheric.precipitation = 0.0
            
        elif condition == WeatherCondition.RAIN:
            self.atmospheric.cloud_cover = 0.9
            self.atmospheric.visibility = 2000.0
            self.atmospheric.precipitation = 5.0
            self.atmospheric.humidity = 0.9
            
        elif condition == WeatherCondition.SNOW:
            self.atmospheric.cloud_cover = 0.8
            self.atmospheric.visibility = 1000.0
            self.atmospheric.precipitation = 3.0
            self.atmospheric.temperature = -2.0
            
        elif condition == WeatherCondition.FOG:
            self.atmospheric.cloud_cover = 0.5
            self.atmospheric.visibility = 200.0
            self.atmospheric.humidity = 0.95
            
        elif condition == WeatherCondition.STORM:
            self.atmospheric.cloud_cover = 1.0
            self.atmospheric.visibility = 500.0
            self.atmospheric.precipitation = 20.0
            self.atmospheric.wind_speed = 15.0
            self.atmospheric.humidity = 0.9
            
        # Update light level based on weather and time of day
        await self._update_light_level()
    
    async def update_time_of_day(self, time_of_day: TimeOfDay) -> None:
        """Update time of day and related properties"""
        self.time_of_day = time_of_day
        
        # Update light level based on time of day
        await self._update_light_level()
    
    async def _update_light_level(self) -> None:
        """Update light level based on weather and time of day"""
        # Base light level from time of day
        if self.time_of_day == TimeOfDay.DAY:
            base_light = 1.0
        elif self.time_of_day == TimeOfDay.DAWN or self.time_of_day == TimeOfDay.DUSK:
            base_light = 0.5
        else:  # NIGHT
            base_light = 0.1
            
        # Modify based on weather
        weather_factor = 1.0
        if self.weather == WeatherCondition.CLOUDY:
            weather_factor = 0.7
        elif self.weather == WeatherCondition.RAIN:
            weather_factor = 0.5
        elif self.weather == WeatherCondition.SNOW:
            weather_factor = 0.6
        elif self.weather == WeatherCondition.FOG:
            weather_factor = 0.4
        elif self.weather == WeatherCondition.STORM:
            weather_factor = 0.3
            
        self.light_level = base_light * weather_factor
    
    async def get_sensor_effectiveness(self, sensor_type: str) -> float:
        """
        Calculate sensor effectiveness based on environmental conditions
        
        Args:
            sensor_type: Type of sensor (e.g., "lidar", "quantum_magnetic", "hyperspectral")
            
        Returns:
            Effectiveness factor (0-1 scale)
        """
        if sensor_type == "lidar":
            # LIDAR affected by precipitation and fog
            return max(0.1, 1.0 - (self.atmospheric.precipitation / 20.0) - 
                      (10000.0 - min(10000.0, self.atmospheric.visibility)) / 10000.0)
                      
        elif sensor_type == "quantum_magnetic":
            # Quantum magnetic sensors affected by EM interference
            return max(0.2, 1.0 - self.em_interference)
            
        elif sensor_type == "hyperspectral":
            # Hyperspectral affected by light level and cloud cover
            return max(0.1, self.light_level * (1.0 - self.atmospheric.cloud_cover * 0.5))
            
        elif sensor_type == "rangefinder":
            # Rangefinder affected by precipitation
            return max(0.3, 1.0 - (self.atmospheric.precipitation / 30.0))
            
        elif sensor_type == "video":
            # Video affected by light level and visibility
            return max(0.1, self.light_level * 
                      (self.atmospheric.visibility / 10000.0))
                      
        return 1.0  # Default for unknown sensor types
    
    async def set_em_interference(self, level: float) -> None:
        """Set electromagnetic interference level (0-1 scale)"""
        self.em_interference = max(0.0, min(1.0, level))
    
    async def calculate_signal_attenuation(self, frequency_mhz: float, distance_km: float) -> float:
        """
        Calculate signal attenuation based on environmental conditions
        
        Args:
            frequency_mhz: Signal frequency in MHz
            distance_km: Distance in kilometers
            
        Returns:
            Attenuation in dB
        """
        # Free space path loss
        fspl = 20 * np.log10(distance_km) + 20 * np.log10(frequency_mhz) + 32.44
        
        # Additional attenuation from weather
        weather_attenuation = 0.0
        
        if self.weather == WeatherCondition.RAIN:
            # Rain attenuation increases with frequency
            rain_factor = 0.01 * (frequency_mhz / 1000.0)**2
            weather_attenuation = rain_factor * self.atmospheric.precipitation * distance_km
            
        elif self.weather == WeatherCondition.FOG:
            # Fog attenuation for high frequencies
            if frequency_mhz > 10000:  # Above 10 GHz
                fog_factor = 0.5 * (frequency_mhz / 10000.0)
                visibility_km = self.atmospheric.visibility / 1000.0
                weather_attenuation = fog_factor * (10.0 / visibility_km) * distance_km
                
        return fspl + weather_attenuation