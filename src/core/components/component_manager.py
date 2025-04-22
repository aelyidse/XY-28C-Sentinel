from typing import Dict, List, Type, Any, Optional
import importlib
import inspect
import os
import logging
from .component_interface import Component

class ComponentManager:
    """
    Central manager for loading and managing components throughout the system.
    """
    def __init__(self):
        self._components: Dict[str, Component] = {}
        self._component_types: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
        
    async def load_component(self, component_class: Type[Component], component_id: str = None) -> Optional[str]:
        """
        Load a component instance from a component class.
        
        Args:
            component_class: The component class to instantiate
            component_id: Optional custom ID for the component
            
        Returns:
            The component ID if successfully loaded, None otherwise
        """
        try:
            # Use provided ID or generate from class name
            if not component_id:
                component_id = f"{component_class.__module__}.{component_class.__name__}"
                
            # Create component instance
            component = component_class()
            
            # Initialize component
            await component.initialize()
            
            # Register component
            self._components[component_id] = component
            
            # Register component type
            component_type = component.get_component_type()
            if component_type not in self._component_types:
                self._component_types[component_type] = []
            self._component_types[component_type].append(component_id)
            
            self.logger.info(f"Loaded component: {component_id} of type {component_type}")
            return component_id
            
        except Exception as e:
            self.logger.error(f"Failed to load component {component_class.__name__}: {str(e)}")
            return None
    
    async def load_components_from_directory(self, directory: str) -> List[str]:
        """
        Discover and load all components from a directory.
        
        Args:
            directory: Directory path to scan for components
            
        Returns:
            List of loaded component IDs
        """
        loaded_components = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.relpath(module_path, directory))[0]
                    module_name = module_name.replace(os.path.sep, '.')
                    
                    try:
                        # Import the module
                        module = importlib.import_module(f"{directory}.{module_name}")
                        
                        # Find component classes in the module
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, Component) and 
                                obj != Component):
                                
                                component_id = await self.load_component(obj)
                                if component_id:
                                    loaded_components.append(component_id)
                                    
                    except Exception as e:
                        self.logger.error(f"Error loading module {module_name}: {str(e)}")
        
        return loaded_components
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by its ID"""
        return self._components.get(component_id)
    
    def get_components_by_type(self, component_type: str) -> List[Component]:
        """Get all components of a specific type"""
        component_ids = self._component_types.get(component_type, [])
        return [self._components[cid] for cid in component_ids if cid in self._components]
    
    def get_all_components(self) -> Dict[str, Component]:
        """Get all registered components"""
        return self._components.copy()
    
    async def shutdown_all_components(self) -> None:
        """Properly shutdown all components"""
        for component_id, component in self._components.items():
            try:
                await component.shutdown()
                self.logger.info(f"Shutdown component: {component_id}")
            except Exception as e:
                self.logger.error(f"Error shutting down component {component_id}: {str(e)}")