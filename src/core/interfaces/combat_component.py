from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from .system_component import SystemComponent

class CombatComponent(SystemComponent, ABC):
    """Base interface for all combat-related components"""
    
    @abstractmethod
    async def arm(self) -> bool:
        """Arm the combat component"""
        pass
        
    @abstractmethod
    async def disarm(self) -> bool:
        """Disarm the combat component"""
        pass
    
    @abstractmethod
    async def get_readiness_status(self) -> Dict[str, Any]:
        """Get the current readiness status of the combat component"""
        pass