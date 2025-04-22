from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Plugin(ABC):
    """
    Base interface for all plugins in the system.
    """
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources when shutting down"""
        pass
    
    @abstractmethod
    def get_plugin_type(self) -> str:
        """Get the type of this plugin"""
        pass
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about this plugin"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get the capabilities provided by this plugin"""
        pass