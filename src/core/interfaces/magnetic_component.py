from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from .system_component import SystemComponent
from .plugin import Plugin

class MagneticComponent(SystemComponent, Plugin):
    """Interface for components that interact with magnetic fields"""
    
    @abstractmethod
    async def measure_field(self, position: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Measure magnetic field at a specific position
        
        Args:
            position: 3D position vector [x, y, z]
            
        Returns:
            Tuple of (field_vector, uncertainty)
        """
        pass
    
    @abstractmethod
    async def generate_field(self, field_params: Dict[str, Any]) -> bool:
        """
        Generate a magnetic field with specified parameters
        
        Args:
            field_params: Parameters defining the field to generate
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def analyze_field_data(self, field_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Analyze magnetic field data
        
        Args:
            field_data: Magnetic field data to analyze
            
        Returns:
            Analysis results
        """
        pass
    
    def get_plugin_type(self) -> str:
        return "magnetic"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "type": "magnetic",
            "capabilities": self.get_capabilities()
        }