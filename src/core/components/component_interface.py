from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Component(ABC):
    """
    Base interface for all components in the system.
    """
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources when shutting down"""
        pass
    
    @abstractmethod
    def get_component_type(self) -> str:
        """Get the type of this component"""
        pass
    
    @abstractmethod
    def get_component_info(self) -> Dict[str, Any]:
        """Get information about this component"""
        pass
    
    @abstractmethod
    def get_services(self) -> List[str]:
        """Get the services provided by this component"""
        pass