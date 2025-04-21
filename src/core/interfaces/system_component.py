from abc import ABC, abstractmethod
from typing import Any, Dict
from ..events.event_manager import EventManager

class SystemComponent(ABC):
    def __init__(self, component_id: str, event_manager: EventManager):
        self.component_id = component_id
        self.event_manager = event_manager
        self._state: Dict[str, Any] = {}
        
    @abstractmethod
    async def initialize(self) -> None:
        pass
        
    @abstractmethod
    async def update(self) -> None:
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        pass
    
    async def get_state(self) -> Dict[str, Any]:
        return self._state.copy()