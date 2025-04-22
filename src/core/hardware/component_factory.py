"""
Hardware Component Factory Module

This module provides a factory for creating hardware components.
"""
from typing import Dict, Any, Optional, Type
import logging
from .component import HardwareComponent
from .control_unit import ControlUnit
from .navigation_system import NavigationSystem
from .sensor import Sensor, SensorType

class ComponentFactory:
    """Factory for creating hardware components"""
    
    @staticmethod
    def create_component(component_type: str, component_id: str, config: Dict[str, Any] = None) -> Optional[HardwareComponent]:
        """
        Create a hardware component of the specified type.
        
        Args:
            component_type: Type of component to create
            component_id: Unique identifier for the component
            config: Configuration for the component
            
        Returns:
            Created component instance or None if type is invalid
        """
        logger = logging.getLogger("sentinel.hardware.factory")
        config = config or {}
        
        if component_type == "control_unit":
            return ControlUnit(component_id, config)
            
        elif component_type == "navigation_system":
            return NavigationSystem(component_id, config)
            
        elif component_type == "sensor":
            sensor_type_str = config.get("sensor_type", "TEMPERATURE")
            try:
                sensor_type = SensorType[sensor_type_str]
                return Sensor(component_id, sensor_type, config)
            except KeyError:
                logger.error(f"Invalid sensor type: {sensor_type_str}")
                return None
                
        else:
            logger.error(f"Unknown component type: {component_type}")
            return None