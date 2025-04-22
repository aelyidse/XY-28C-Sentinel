from typing import Dict, List, Any, Optional, Type
import os
import logging
from .component_manager import ComponentManager
from .component_registry import ComponentRegistry
from .component_interface import Component

class ComponentSystem:
    """
    Main entry point for the component system
    """
    def __init__(self, component_dirs: List[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if component_dirs is None:
            component_dirs = ["src/components"]
            
        self.component_dirs = component_dirs
        self.component_manager = ComponentManager()
        self.component_registry = ComponentRegistry()
        
    async def initialize(self) -> None:
        """Initialize the component system"""
        self.logger.info("Initializing component system")
        
        # Load components from all component directories
        for component_dir in self.component_dirs:
            if os.path.exists(component_dir):
                self.logger.info(f"Loading components from {component_dir}")
                loaded_components = await self.component_manager.load_components_from_directory(component_dir)
                self.logger.info(f"Loaded {len(loaded_components)} components from {component_dir}")
                
                # Register loaded components
                for component_id in loaded_components:
                    component = self.component_manager.get_component(component_id)
                    if component:
                        self.component_registry.register_component(
                            component_id,
                            component.get_component_info()
                        )
            else:
                self.logger.warning(f"Component directory not found: {component_dir}")
                
    async def shutdown(self) -> None:
        """Shutdown the component system"""
        self.logger.info("Shutting down component system")
        await self.component_manager.shutdown_all_components()
        
    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by ID"""
        return self.component_manager.get_component(component_id)
        
    def get_components_by_type(self, component_type: str) -> List[Component]:
        """Get all components of a specific type"""
        return self.component_manager.get_components_by_type(component_type)
        
    def get_components_by_service(self, service: str) -> List[Component]:
        """Get all components that provide a specific service"""
        component_ids = self.component_registry.find_components_by_service(service)
        return [self.component_manager.get_component(cid) for cid in component_ids 
                if self.component_manager.get_component(cid)]
        
    async def load_component(self, component_class: Type[Component], component_id: str = None) -> Optional[str]:
        """Load a component"""
        return await self.component_manager.load_component(component_class, component_id)