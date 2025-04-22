from typing import Dict, Any, Optional
import json
import os
import logging

class PluginConfig:
    """
    Configuration manager for plugins
    """
    def __init__(self, config_dir: str = "config/plugins"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        self._configs: Dict[str, Dict[str, Any]] = {}
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
    def load_config(self, plugin_id: str) -> Dict[str, Any]:
        """
        Load configuration for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            Configuration dictionary
        """
        if plugin_id in self._configs:
            return self._configs[plugin_id]
            
        config_path = os.path.join(self.config_dir, f"{plugin_id}.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self._configs[plugin_id] = config
                    return config
        except Exception as e:
            self.logger.error(f"Error loading config for {plugin_id}: {str(e)}")
            
        # Return empty config if not found or error
        self._configs[plugin_id] = {}
        return {}
        
    def save_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for a specific plugin
        
        Args:
            plugin_id: Plugin identifier
            config: Configuration to save
            
        Returns:
            Success status
        """
        try:
            config_path = os.path.join(self.config_dir, f"{plugin_id}.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            self._configs[plugin_id] = config
            return True
        except Exception as e:
            self.logger.error(f"Error saving config for {plugin_id}: {str(e)}")
            return False
            
    def update_config(self, plugin_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in a plugin's configuration
        
        Args:
            plugin_id: Plugin identifier
            updates: Fields to update
            
        Returns:
            Success status
        """
        current_config = self.load_config(plugin_id)
        current_config.update(updates)
        return self.save_config(plugin_id, current_config)