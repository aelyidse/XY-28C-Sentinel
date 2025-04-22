from typing import Dict, List, Any, Optional, Type
import os
import logging
from .plugin_manager import PluginManager
from .plugin_config import PluginConfig
from .plugin_registry import PluginRegistry
from ..interfaces.plugin import Plugin

class PluginSystem:
    """
    Main entry point for the plugin system
    """
    def __init__(self, plugin_dirs: List[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if plugin_dirs is None:
            plugin_dirs = ["src/plugins"]
            
        self.plugin_dirs = plugin_dirs
        self.plugin_manager = PluginManager()
        self.plugin_config = PluginConfig()
        self.plugin_registry = PluginRegistry()
        
    async def initialize(self) -> None:
        """Initialize the plugin system"""
        self.logger.info("Initializing plugin system")
        
        # Load plugins from all plugin directories
        for plugin_dir in self.plugin_dirs:
            if os.path.exists(plugin_dir):
                self.logger.info(f"Loading plugins from {plugin_dir}")
                loaded_plugins = await self.plugin_manager.load_plugins_from_directory(plugin_dir)
                self.logger.info(f"Loaded {len(loaded_plugins)} plugins from {plugin_dir}")
                
                # Register loaded plugins
                for plugin_id in loaded_plugins:
                    plugin = self.plugin_manager.get_plugin(plugin_id)
                    if plugin:
                        self.plugin_registry.register_plugin(
                            plugin_id,
                            plugin.get_plugin_info()
                        )
            else:
                self.logger.warning(f"Plugin directory not found: {plugin_dir}")
                
    async def shutdown(self) -> None:
        """Shutdown the plugin system"""
        self.logger.info("Shutting down plugin system")
        await self.plugin_manager.shutdown_all_plugins()
        
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID"""
        return self.plugin_manager.get_plugin(plugin_id)
        
    def get_plugins_by_type(self, plugin_type: str) -> List[Plugin]:
        """Get all plugins of a specific type"""
        return self.plugin_manager.get_plugins_by_type(plugin_type)
        
    def get_plugins_by_capability(self, capability: str) -> List[Plugin]:
        """Get all plugins that provide a specific capability"""
        plugin_ids = self.plugin_registry.find_plugins_by_capability(capability)
        return [self.plugin_manager.get_plugin(pid) for pid in plugin_ids if self.plugin_manager.get_plugin(pid)]
        
    async def load_plugin(self, plugin_class: Type[Plugin], plugin_id: str = None) -> Optional[str]:
        """Load a plugin"""
        return await self.plugin_manager.load_plugin(plugin_class, plugin_id)