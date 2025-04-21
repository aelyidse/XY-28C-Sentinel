import importlib
from typing import Dict, Type
from ..interfaces.system_component import SystemComponent

class PluginManager:
    def __init__(self):
        self._plugins: Dict[str, Type[SystemComponent]] = {}
        
    def register_plugin(self, name: str, plugin_class: Type[SystemComponent]) -> None:
        self._plugins[name] = plugin_class
        
    def load_plugin(self, module_path: str, class_name: str) -> Type[SystemComponent]:
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)
        self.register_plugin(class_name, plugin_class)
        return plugin_class
        
    def get_plugin(self, name: str) -> Type[SystemComponent]:
        return self._plugins[name]