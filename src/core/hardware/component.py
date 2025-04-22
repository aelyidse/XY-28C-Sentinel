"""
Base Hardware Component Module

This module defines the base interface for all hardware components in the XY-28C-Sentinel system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
import asyncio

class ComponentStatus(Enum):
    """Status of a hardware component"""
    OFFLINE = 0
    INITIALIZING = 1
    ONLINE = 2
    DEGRADED = 3
    ERROR = 4
    MAINTENANCE = 5

class HardwareComponent(ABC):
    """Base class for all hardware components"""
    
    def __init__(self, component_id: str, config: Dict[str, Any] = None):
        self.component_id = component_id
        self.config = config or {}
        self.status = ComponentStatus.OFFLINE
        self.diagnostics = {}
        self._last_update = 0
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the hardware component"""
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the hardware component"""
        pass
        
    @abstractmethod
    async def update(self) -> None:
        """Update component state"""
        pass
        
    @abstractmethod
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information from the component"""
        pass
        
    async def set_configuration(self, config: Dict[str, Any]) -> bool:
        """Update component configuration"""
        self.config.update(config)
        return True
        
    async def get_status(self) -> ComponentStatus:
        """Get current component status"""
        return self.status