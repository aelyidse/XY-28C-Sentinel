"""
XY-28C-Sentinel SDK Core Module

This module provides the main entry point for the XY-28C-Sentinel SDK.
"""
import asyncio
import logging
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, Type, List, Callable

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

@dataclass
class SDKConfig:
    """Configuration for the XY-28C-Sentinel SDK"""
    log_level: LogLevel = LogLevel.INFO
    plugin_directories: List[str] = None
    config_file: Optional[str] = None
    enable_telemetry: bool = True
    enable_blockchain: bool = True
    enable_ai_components: bool = True
    max_concurrent_operations: int = 10
    timeout_seconds: float = 30.0
    
    def __post_init__(self):
        if self.plugin_directories is None:
            self.plugin_directories = ["plugins"]

class SentinelSDK:
    """
    Main entry point for the XY-28C-Sentinel SDK.
    
    This class provides access to all SDK functionality and manages the lifecycle
    of SDK components.
    
    Example:
        ```python
        # Initialize the SDK
        sdk = SentinelSDK()
        await sdk.initialize()
        
        # Get a component
        mission_controller = sdk.get_component("mission_controller")
        
        # Use the component
        result = await mission_controller.execute_mission(params)
        
        # Shutdown the SDK
        await sdk.shutdown()
        ```
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SentinelSDK, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[SDKConfig] = None):
        if self._initialized:
            return
            
        self.config = config or SDKConfig()
        self._components = {}
        self._event_listeners = {}
        self._plugin_manager = None
        self._system_controller = None
        self._logger = None
        self._initialized = False
        self._rbac_manager = None
    
    @classmethod
    def from_config_file(cls, config_file: str) -> 'SentinelSDK':
        """
        Initialize the SDK from a configuration file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            Initialized SDK instance
        """
        with open(config_file, 'r') as f:
            config_dict = json.load(f)
        
        config = SDKConfig(
            log_level=LogLevel[config_dict.get('log_level', 'INFO')],
            plugin_directories=config_dict.get('plugin_directories', ["plugins"]),
            config_file=config_file,
            enable_telemetry=config_dict.get('enable_telemetry', True),
            enable_blockchain=config_dict.get('enable_blockchain', True),
            enable_ai_components=config_dict.get('enable_ai_components', True),
            max_concurrent_operations=config_dict.get('max_concurrent_operations', 10),
            timeout_seconds=config_dict.get('timeout_seconds', 30.0)
        )
        
        return cls(config)
    
    async def initialize(self) -> None:
        """
        Initialize the SDK and all its components.
        
        This method must be called before using any SDK functionality.
        """
        if self._initialized:
            return
            
        # Set up logging
        self._setup_logging()
        
        # Import components here to avoid circular imports
        from ..system.plugin_manager import PluginManager
        from ..system.system_controller import SystemController
        from ..system.event_manager import EventManager
        
        # Initialize core components
        self._plugin_manager = PluginManager()
        self._event_manager = EventManager()
        
        # Load system configuration
        from ..config.system_config import SystemConfig
        system_config = SystemConfig.default_config()
        
        # Initialize system controller
        self._system_controller = SystemController(
            event_manager=self._event_manager,
            plugin_manager=self._plugin_manager,
            config=system_config
        )
        
        # Register core components
        self._register_core_components()
        
        # Load plugins
        await self._load_plugins()
        
        # Initialize system controller
        await self._system_controller.initialize()
        
        self._initialized = True
        self._logger.info("XY-28C-Sentinel SDK initialized successfully")
    
    async def shutdown(self) -> None:
        """
        Shutdown the SDK and all its components.
        
        This method should be called when the SDK is no longer needed.
        """
        if not self._initialized:
            return
            
        # Shutdown system controller
        await self._system_controller.shutdown()
        
        # Clear components
        self._components.clear()
        self._event_listeners.clear()
        
        self._initialized = False
        self._logger.info("XY-28C-Sentinel SDK shutdown successfully")
    
    def get_component(self, component_id: str) -> Any:
        """
        Get a component by its ID.
        
        Args:
            component_id: ID of the component to get
            
        Returns:
            The component instance
            
        Raises:
            ValueError: If the component does not exist
        """
        if not self._initialized:
            raise RuntimeError("SDK not initialized. Call initialize() first.")
            
        if component_id not in self._components:
            raise ValueError(f"Component {component_id} not found")
            
        return self._components[component_id]
    
    def register_event_listener(self, event_type: str, listener: Callable) -> None:
        """
        Register a listener for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            listener: Callback function to call when the event occurs
        """
        if not self._initialized:
            raise RuntimeError("SDK not initialized. Call initialize() first.")
            
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
            
        self._event_listeners[event_type].append(listener)
        self._event_manager.subscribe(event_type, listener)
    
    def _setup_logging(self) -> None:
        """Set up logging for the SDK"""
        logging.basicConfig(
            level=self.config.log_level.value,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._logger = logging.getLogger('xy28c_sentinel_sdk')
    
    def _register_core_components(self) -> None:
        """Register core SDK components"""
        # Import core components
        from ..control.mission_controller import MissionController
        from ..comms.blockchain_controller import BlockchainController
        from ..comms.secure_protocol import SecureProtocol
        
        # Create and register components
        blockchain_controller = BlockchainController()
        self._components['blockchain_controller'] = blockchain_controller
        
        secure_protocol = SecureProtocol()
        self._components['secure_protocol'] = secure_protocol
        
        mission_controller = MissionController(blockchain_controller)
        self._components['mission_controller'] = mission_controller
    
    async def _load_plugins(self) -> None:
        """Load plugins from configured directories"""
        for plugin_dir in self.config.plugin_directories:
            if not os.path.exists(plugin_dir):
                self._logger.warning(f"Plugin directory {plugin_dir} does not exist")
                continue
                
            for filename in os.listdir(plugin_dir):
                if filename.endswith('.py') and not filename.startswith('_'):
                    module_name = filename[:-3]
                    try:
                        plugin_class = self._plugin_manager.load_plugin(
                            f"plugins.{module_name}",
                            f"{module_name.capitalize()}Plugin"
                        )
                        plugin = plugin_class(self._event_manager)
                        self._components[module_name] = plugin
                        self._logger.info(f"Loaded plugin: {module_name}")
                    except Exception as e:
                        self._logger.error(f"Failed to load plugin {module_name}: {e}")
    
    def check_permission(self, role: str, resource: str, action: str) -> bool:
        """
        Check if a role has permission to perform an action on a resource.
        
        Args:
            role: Role name
            resource: Resource identifier
            action: Action to perform
            
        Returns:
            True if permitted, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("SDK not initialized. Call initialize() first.")
            
        from .security.rbac import Role
        try:
            role_enum = Role(role.lower())
            return self._rbac_manager.check_permission(role_enum, resource, action)
        except ValueError:
            return False