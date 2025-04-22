"""
Environment Controller Module

This module provides the main controller for terrain and environment modeling
in the XY-28C-Sentinel system.
"""

from typing import Dict, List, Tuple, Optional, Any
import asyncio
import numpy as np
from ..system.system_controller import SystemController
from ..system.events import SystemEvent, SystemEventType
from ..utils.error_handler import SentinelError, ErrorCategory, ErrorSeverity
from .terrain_model import TerrainModel, TerrainType, TerrainProperties
from .environment_model import EnvironmentModel, WeatherCondition, TimeOfDay

class EnvironmentController:
    """Environment controller for XY-28C-Sentinel"""
    
    def __init__(self, system_controller: SystemController):
        """
        Initialize environment controller
        
        Args:
            system_controller: System controller instance
        """
        self.system_controller = system_controller
        self.terrain_model = None
        self.environment_model = EnvironmentModel()
        
    async def initialize(self, terrain_dimensions: Tuple[int, int], resolution: float = 1.0) -> bool:
        """
        Initialize environment controller
        
        Args:
            terrain_dimensions: Terrain grid dimensions (width, height)
            resolution: Spatial resolution in meters per grid cell
            
        Returns:
            Success status
        """
        try:
            # Initialize terrain model
            self.terrain_model = TerrainModel(terrain_dimensions, resolution)
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Notify system of initialization
            await self._notify_initialization()
            
            return True
            
        except Exception as e:
            raise SentinelError(
                f"Failed to initialize environment controller: {str(e)}",
                category=ErrorCategory.SOFTWARE,
                severity=ErrorSeverity.ERROR
            )
    
    async def _register_event_handlers(self) -> None:
        """Register event handlers"""
        # Register for relevant system events
        self.system_controller.event_manager.subscribe(
            SystemEventType.SENSOR_DATA_UPDATED,
            self._handle_sensor_data_updated
        )
        
        self.system_controller.event_manager.subscribe(
            SystemEventType.NAVIGATION_POSITION_UPDATED,
            self._handle_position_updated
        )
    
    async def _notify_initialization(self) -> None:
        """Notify system of environment controller initialization"""
        await self.system_controller.event_manager.publish(
            SystemEvent(
                event_type=SystemEventType.COMPONENT_INITIALIZED,
                component_id="environment_controller",
                data={
                    "terrain_dimensions": self.terrain_model.dimensions,
                    "resolution": self.terrain_model.resolution
                },
                priority=2
            )
        )
    
    async def _handle_sensor_data_updated(self, event: SystemEvent) -> None:
        """Handle sensor data updated event"""
        # Update environment model based on sensor data
        pass
    
    async def _handle_position_updated(self, event: SystemEvent) -> None:
        """Handle position updated event"""
        # Update terrain information at current position
        pass
    
    async def load_terrain_data(self, elevation_data: np.ndarray) -> bool:
        """
        Load terrain elevation data
        
        Args:
            elevation_data: Numpy array of elevation data
            
        Returns:
            Success status
        """
        if self.terrain_model is None:
            return False
            
        return await self.terrain_model.load_elevation_data(elevation_data)
    
    async def set_weather_condition(self, condition: WeatherCondition) -> None:
        """Set current weather condition"""
        await self.environment_model.update_weather(condition)
        
        # Notify system of weather change
        await self.system_controller.event_manager.publish(
            SystemEvent(
                event_type=SystemEventType.ENVIRONMENT_UPDATED,
                component_id="environment_controller",
                data={
                    "weather": condition.value,
                    "visibility": self.environment_model.atmospheric.visibility,
                    "precipitation": self.environment_model.atmospheric.precipitation
                },
                priority=2
            )
        )
    
    async def set_time_of_day(self, time_of_day: TimeOfDay) -> None:
        """Set current time of day"""
        await self.environment_model.update_time_of_day(time_of_day)
        
        # Notify system of time change
        await self.system_controller.event_manager.publish(
            SystemEvent(
                event_type=SystemEventType.ENVIRONMENT_UPDATED,
                component_id="environment_controller",
                data={
                    "time_of_day": time_of_day.value,
                    "light_level": self.environment_model.light_level
                },
                priority=2
            )
        )
    
    async def get_terrain_info(self, position: Tuple[float, float]) -> Dict[str, Any]:
        """
        Get terrain information at a specific position
        
        Args:
            position: Position coordinates (x, y)
            
        Returns:
            Dictionary of terrain information
        """
        if self.terrain_model is None:
            return {}
            
        x, y = position
        elevation = await self.terrain_model.get_elevation(x, y)
        properties = await self.terrain_model.get_terrain_properties(x, y)
        slope = await self.terrain_model.get_slope(x, y)
        
        return {
            "elevation": elevation,
            "slope": slope,
            "friction": properties.friction_coefficient,
            "radar_reflectivity": properties.radar_reflectivity
        }
    
    async def get_environment_info(self) -> Dict[str, Any]:
        """
        Get current environment information
        
        Returns:
            Dictionary of environment information
        """
        return {
            "weather": self.environment_model.weather.value,
            "time_of_day": self.environment_model.time_of_day.value,
            "temperature": self.environment_model.atmospheric.temperature,
            "humidity": self.environment_model.atmospheric.humidity,
            "wind_speed": self.environment_model.atmospheric.wind_speed,
            "wind_direction": self.environment_model.atmospheric.wind_direction,
            "visibility": self.environment_model.atmospheric.visibility,
            "light_level": self.environment_model.light_level
        }
    
    async def check_line_of_sight(self, start: Tuple[float, float, float], 
                                end: Tuple[float, float, float]) -> bool:
        """
        Check if there is line of sight between two points
        
        Args:
            start: Starting point (x, y, z)
            end: Ending point (x, y, z)
            
        Returns:
            True if line of sight exists, False otherwise
        """
        if self.terrain_model is None:
            return True
            
        return await self.terrain_model.calculate_line_of_sight(start, end)
    
    async def get_sensor_effectiveness(self, sensor_type: str, 
                                     position: Tuple[float, float]) -> float:
        """
        Get sensor effectiveness at a specific position
        
        Args:
            sensor_type: Type of sensor
            position: Position coordinates (x, y)
            
        Returns:
            Effectiveness factor (0-1 scale)
        """
        # Get base effectiveness from environment
        base_effectiveness = await self.environment_model.get_sensor_effectiveness(sensor_type)
        
        # Modify based on terrain if needed
        if self.terrain_model is not None:
            properties = await self.terrain_model.get_terrain_properties(*position)
            
            # Apply terrain-specific modifications
            if sensor_type == "lidar" or sensor_type == "rangefinder":
                # These sensors affected by radar reflectivity
                return base_effectiveness * (0.5 + 0.5 * properties.radar_reflectivity)
                
            elif sensor_type == "quantum_magnetic":
                # Quantum sensors affected by terrain density
                density_factor = min(1.0, properties.density / 2000.0)
                return base_effectiveness * (0.7 + 0.3 * density_factor)
                
            elif sensor_type == "hyperspectral":
                # Hyperspectral affected by terrain type
                return base_effectiveness
        
        return base_effectiveness