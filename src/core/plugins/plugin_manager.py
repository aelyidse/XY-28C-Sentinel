from typing import Dict, List, Type, Any, Optional
import importlib
import inspect
import os
import logging
from ..interfaces.plugin import Plugin

class PluginManager:
    """
    Central manager for loading and managing plugins throughout the system.
    """
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_types: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
        
    async def load_plugin(self, plugin_class: Type[Plugin], plugin_id: str = None) -> Optional[str]:
        """
        Load a plugin instance from a plugin class.
        
        Args:
            plugin_class: The plugin class to instantiate
            plugin_id: Optional custom ID for the plugin
            
        Returns:
            The plugin ID if successfully loaded, None otherwise
        """
        try:
            # Use provided ID or generate from class name
            if not plugin_id:
                plugin_id = f"{plugin_class.__module__}.{plugin_class.__name__}"
                
            # Create plugin instance
            plugin = plugin_class()
            
            # Initialize plugin
            await plugin.initialize()
            
            # Register plugin
            self._plugins[plugin_id] = plugin
            
            # Register plugin type
            plugin_type = plugin.get_plugin_type()
            if plugin_type not in self._plugin_types:
                self._plugin_types[plugin_type] = []
            self._plugin_types[plugin_type].append(plugin_id)
            
            self.logger.info(f"Loaded plugin: {plugin_id} of type {plugin_type}")
            return plugin_id
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_class.__name__}: {str(e)}")
            return None
    
    async def load_plugins_from_directory(self, directory: str) -> List[str]:
        """
        Discover and load all plugins from a directory.
        
        Args:
            directory: Directory path to scan for plugins
            
        Returns:
            List of loaded plugin IDs
        """
        loaded_plugins = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.relpath(module_path, directory))[0]
                    module_name = module_name.replace(os.path.sep, '.')
                    
                    try:
                        # Import the module
                        module = importlib.import_module(f"{directory}.{module_name}")
                        
                        # Find plugin classes in the module
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, Plugin) and 
                                obj != Plugin):
                                
                                plugin_id = await self.load_plugin(obj)
                                if plugin_id:
                                    loaded_plugins.append(plugin_id)
                                    
                    except Exception as e:
                        self.logger.error(f"Error loading module {module_name}: {str(e)}")
        
        return loaded_plugins
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by its ID"""
        return self._plugins.get(plugin_id)
    
    def get_plugins_by_type(self, plugin_type: str) -> List[Plugin]:
        """Get all plugins of a specific type"""
        plugin_ids = self._plugin_types.get(plugin_type, [])
        return [self._plugins[pid] for pid in plugin_ids if pid in self._plugins]
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """Get all registered plugins"""
        return self._plugins.copy()
    
    async def shutdown_all_plugins(self) -> None:
        """Properly shutdown all plugins"""
        for plugin_id, plugin in self._plugins.items():
            try:
                await plugin.shutdown()
                self.logger.info(f"Shutdown plugin: {plugin_id}")
            except Exception as e:
                self.logger.error(f"Error shutting down plugin {plugin_id}: {str(e)}")