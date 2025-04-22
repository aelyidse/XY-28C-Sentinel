from typing import Dict, List, Any, Optional, Type
import json
import os
import logging
from ..interfaces.plugin import Plugin

class PluginRegistry:
    """
    Registry for plugin metadata and discovery
    """
    def __init__(self, registry_path: str = "config/plugin_registry.json"):
        self.registry_path = registry_path
        self.logger = logging.getLogger(__name__)
        self._registry: Dict[str, Dict[str, Any]] = {}
        
        # Load existing registry if it exists
        self._load_registry()
        
    def register_plugin(self, plugin_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Register a plugin with metadata
        
        Args:
            plugin_id: Plugin identifier
            metadata: Plugin metadata
            
        Returns:
            Success status
        """
        self._registry[plugin_id] = metadata
        return self._save_registry()
        
    def unregister_plugin(self, plugin_id: str) -> bool:
        """
        Remove a plugin from the registry
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Success status
        """
        if plugin_id in self._registry:
            del self._registry[plugin_id]
            return self._save_registry()
        return False
        
    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Plugin metadata or None if not found
        """
        return self._registry.get(plugin_id)
        
    def find_plugins_by_type(self, plugin_type: str) -> List[str]:
        """
        Find all plugins of a specific type
        
        Args:
            plugin_type: Plugin type to search for
            
        Returns:
            List of plugin IDs matching the type
        """
        return [
            pid for pid, metadata in self._registry.items()
            if metadata.get("type") == plugin_type
        ]
        
    def find_plugins_by_capability(self, capability: str) -> List[str]:
        """
        Find all plugins that provide a specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of plugin IDs providing the capability
        """
        return [
            pid for pid, metadata in self._registry.items()
            if capability in metadata.get("capabilities", [])
        ]
        
    def _load_registry(self) -> None:
        """Load the plugin registry from disk"""
        try:
            if os.path.exists(self.registry_path):
                with open(self.registry_path, 'r') as f:
                    self._registry = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading plugin registry: {str(e)}")
            self._registry = {}
            
    def _save_registry(self) -> bool:
        """Save the plugin registry to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            
            with open(self.registry_path, 'w') as f:
                json.dump(self._registry, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving plugin registry: {str(e)}")
            return False