from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, Union
from enum import Enum
from .combat_component import CombatComponent

class ExplosiveType(Enum):
    """Types of explosive components"""
    SHAPED_CHARGE = 0
    FRAGMENTATION = 1
    THERMOBARIC = 2
    EMP = 3

class ExplosiveComponent(CombatComponent, ABC):
    """Interface for explosive combat components"""
    
    @abstractmethod
    async def set_yield(self, yield_value: float) -> bool:
        """Set the explosive yield"""
        pass
    
    @abstractmethod
    async def get_explosive_type(self) -> ExplosiveType:
        """Get the type of explosive"""
        pass
    
    @abstractmethod
    async def trigger(self, delay_ms: int = 0) -> bool:
        """Trigger the explosive with optional delay in milliseconds"""
        pass