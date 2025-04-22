"""
Terrain Modeling Module

This module provides terrain representation and analysis capabilities for the XY-28C-Sentinel system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import asyncio

class TerrainType(Enum):
    """Types of terrain surfaces"""
    FLAT = "flat"
    URBAN = "urban"
    MOUNTAINOUS = "mountainous"
    FOREST = "forest"
    DESERT = "desert"
    WATER = "water"
    CUSTOM = "custom"

@dataclass
class TerrainProperties:
    """Physical properties of terrain"""
    friction_coefficient: float = 0.5
    radar_reflectivity: float = 0.3
    thermal_conductivity: float = 0.2
    density: float = 1500.0  # kg/m³
    em_absorption: float = 0.4  # Electromagnetic absorption coefficient
    
    @classmethod
    def for_terrain_type(cls, terrain_type: TerrainType) -> 'TerrainProperties':
        """Get default properties for a terrain type"""
        if terrain_type == TerrainType.FLAT:
            return cls(friction_coefficient=0.4, radar_reflectivity=0.2)
        elif terrain_type == TerrainType.URBAN:
            return cls(friction_coefficient=0.7, radar_reflectivity=0.8)
        elif terrain_type == TerrainType.MOUNTAINOUS:
            return cls(friction_coefficient=0.6, radar_reflectivity=0.5)
        elif terrain_type == TerrainType.FOREST:
            return cls(friction_coefficient=0.5, radar_reflectivity=0.3, em_absorption=0.7)
        elif terrain_type == TerrainType.DESERT:
            return cls(friction_coefficient=0.3, radar_reflectivity=0.4, thermal_conductivity=0.1)
        elif terrain_type == TerrainType.WATER:
            return cls(friction_coefficient=0.1, radar_reflectivity=0.9, density=1000.0)
        else:
            return cls()

class TerrainModel:
    """Terrain model for XY-28C-Sentinel"""
    
    def __init__(self, dimensions: Tuple[int, int], resolution: float = 1.0):
        """
        Initialize terrain model
        
        Args:
            dimensions: Grid dimensions (width, height)
            resolution: Spatial resolution in meters per grid cell
        """
        self.dimensions = dimensions
        self.resolution = resolution
        self.elevation_data = np.zeros(dimensions)
        self.terrain_types = np.full(dimensions, TerrainType.FLAT.value)
        self.properties_map = {}
        
        # Initialize default properties for each terrain type
        for terrain_type in TerrainType:
            self.properties_map[terrain_type.value] = TerrainProperties.for_terrain_type(terrain_type)
    
    async def load_elevation_data(self, data: np.ndarray) -> bool:
        """Load elevation data into the model"""
        if data.shape != self.dimensions:
            return False
        
        self.elevation_data = data
        return True
    
    async def set_terrain_type(self, x: int, y: int, terrain_type: TerrainType) -> None:
        """Set terrain type for a specific location"""
        if 0 <= x < self.dimensions[0] and 0 <= y < self.dimensions[1]:
            self.terrain_types[x, y] = terrain_type.value
    
    async def get_elevation(self, x: float, y: float) -> float:
        """Get interpolated elevation at a specific location"""
        # Convert to grid coordinates
        grid_x = x / self.resolution
        grid_y = y / self.resolution
        
        # Bilinear interpolation
        x0, y0 = int(grid_x), int(grid_y)
        x1, y1 = min(x0 + 1, self.dimensions[0] - 1), min(y0 + 1, self.dimensions[1] - 1)
        
        dx, dy = grid_x - x0, grid_y - y0
        
        # Interpolate elevation
        elevation = (1 - dx) * (1 - dy) * self.elevation_data[x0, y0] + \
                    dx * (1 - dy) * self.elevation_data[x1, y0] + \
                    (1 - dx) * dy * self.elevation_data[x0, y1] + \
                    dx * dy * self.elevation_data[x1, y1]
                    
        return elevation
    
    async def get_terrain_properties(self, x: float, y: float) -> TerrainProperties:
        """Get terrain properties at a specific location"""
        # Convert to grid coordinates
        grid_x = int(x / self.resolution)
        grid_y = int(y / self.resolution)
        
        # Clamp to valid range
        grid_x = max(0, min(grid_x, self.dimensions[0] - 1))
        grid_y = max(0, min(grid_y, self.dimensions[1] - 1))
        
        terrain_type = self.terrain_types[grid_x, grid_y]
        return self.properties_map[terrain_type]
    
    async def calculate_line_of_sight(self, start: Tuple[float, float, float], 
                                    end: Tuple[float, float, float]) -> bool:
        """
        Calculate line of sight between two points
        
        Args:
            start: Starting point (x, y, z)
            end: Ending point (x, y, z)
            
        Returns:
            True if line of sight exists, False otherwise
        """
        # Extract coordinates
        start_x, start_y, start_z = start
        end_x, end_y, end_z = end
        
        # Calculate direction vector
        dx = end_x - start_x
        dy = end_y - start_y
        dz = end_z - start_z
        
        # Calculate distance
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        
        # Number of sample points
        num_samples = int(distance / (self.resolution * 0.5))
        
        # Check line of sight
        for i in range(1, num_samples):
            # Calculate sample point
            t = i / num_samples
            x = start_x + t * dx
            y = start_y + t * dy
            z = start_z + t * dz
            
            # Get elevation at sample point
            elevation = await self.get_elevation(x, y)
            
            # Check if sample point is below terrain
            if z < elevation:
                return False
                
        return True
    
    async def get_slope(self, x: float, y: float) -> float:
        """Calculate terrain slope at a specific location"""
        # Convert to grid coordinates
        grid_x = int(x / self.resolution)
        grid_y = int(y / self.resolution)
        
        # Clamp to valid range
        grid_x = max(0, min(grid_x, self.dimensions[0] - 2))
        grid_y = max(0, min(grid_y, self.dimensions[1] - 2))
        
        # Calculate slope using central difference
        dx = self.elevation_data[grid_x + 1, grid_y] - self.elevation_data[grid_x, grid_y]
        dy = self.elevation_data[grid_x, grid_y + 1] - self.elevation_data[grid_x, grid_y]
        
        # Calculate slope magnitude
        return np.sqrt((dx / self.resolution)**2 + (dy / self.resolution)**2)