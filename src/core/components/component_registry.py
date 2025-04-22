from typing import Dict, List, Any, Optional
import json
import os
import logging

class ComponentRegistry:
    """
    Registry for component metadata and discovery
    """
    def __init__(self, registry_path: str = "config/component_registry.json"):
        self.registry_path = registry_path
        self.logger = logging.getLogger(__name__)
        self._registry: Dict[str, Dict[str, Any]] = {}
        
        # Load existing registry if it exists
        self._load_registry()
        
    def register_component(self, component_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Register a component with metadata
        
        Args:
            component_id: Component identifier
            metadata: Component metadata
            
        Returns:
            Success status
        """
        self._registry[component_id] = metadata
        return self._save_registry()
        
    def unregister_component(self, component_id: str) -> bool:
        """
        Remove a component from the registry
        
        Args:
            component_id: Component identifier
            
        Returns:
            Success status
        """
        if component_id in self._registry:
            del self._registry[component_id]
            return self._save_registry()
        return False
        
    def get_component_metadata(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific component
        
        Args:
            component_id: Component identifier
            
        Returns:
            Component metadata or None if not found
        """
        return self._registry.get(component_id)
        
    def find_components_by_type(self, component_type: str) -> List[str]:
        """
        Find all components of a specific type
        
        Args:
            component_type: Component type to search for
            
        Returns:
            List of component IDs matching the type
        """
        return [
            cid for cid, metadata in self._registry.items()
            if metadata.get("type") == component_type
        ]
        
    def find_components_by_service(self, service: str) -> List[str]:
        """
        Find all components that provide a specific service
        
        Args:
            service: Service to search for
            
        Returns:
            List of component IDs providing the service
        """
        return [
            cid for cid, metadata in self._registry.items()
            if service in metadata.get("services", [])
        ]
        
    def _load_registry(self) -> None:
        """Load the component registry from disk"""
        try:
            if os.path.exists(self.registry_path):
                with open(self.registry_path, 'r') as f:
                    self._registry = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading component registry: {str(e)}")
            self._registry = {}
            
    def _save_registry(self) -> bool:
        """Save the component registry to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            
            with open(self.registry_path, 'w') as f:
                json.dump(self._registry, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving component registry: {str(e)}")
            return False