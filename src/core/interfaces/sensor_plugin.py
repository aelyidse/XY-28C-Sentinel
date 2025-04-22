from abc import abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
from .system_component import SystemComponent
from .plugin import Plugin

class SensorPlugin(SystemComponent, Plugin):
    """Interface for sensor plugins"""
    
    @abstractmethod
    async def collect_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect sensor data with specified parameters
        
        Args:
            parameters: Collection parameters
            
        Returns:
            Collected sensor data
        """
        pass
    
    @abstractmethod
    async def calibrate(self, calibration_params: Dict[str, Any]) -> bool:
        """
        Calibrate the sensor
        
        Args:
            calibration_params: Calibration parameters
            
        Returns:
            Success status
        """
        pass
    
    @abstractmethod
    async def get_sensor_specs(self) -> Dict[str, Any]:
        """
        Get sensor specifications
        
        Returns:
            Sensor specifications
        """
        pass
    
    def get_plugin_type(self) -> str:
        return "sensor"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "type": "sensor",
            "capabilities": self.get_capabilities()
        }