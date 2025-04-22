"""
SDK Configuration Module

This module provides configuration management for the XY-28C-Sentinel SDK.
"""
import json
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional

class ConfigurationError(Exception):
    """Exception raised for configuration errors"""
    pass

class SecurityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    MILITARY = 4

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

@dataclass
class NetworkConfig:
    """Network configuration"""
    enable_blockchain: bool = True
    blockchain_nodes: List[str] = field(default_factory=lambda: ["localhost:8545"])
    enable_secure_comms: bool = True
    frequency_hopping: bool = True
    encryption_level: SecurityLevel = SecurityLevel.HIGH

@dataclass
class SensorConfig:
    """Sensor configuration"""
    lidar_enabled: bool = True
    lidar_resolution: float = 0.05  # meters
    hyperspectral_enabled: bool = True
    quantum_magnetic_enabled: bool = True
    update_rate: float = 100.0  # Hz

@dataclass
class AIConfig:
    """AI configuration"""
    enable_llm: bool = True
    enable_context_awareness: bool = True
    enable_autonomous_decisions: bool = True
    max_decision_time: float = 0.5  # seconds
    model_precision: str = "float16"

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: LogLevel = LogLevel.INFO
    file_logging: bool = True
    console_logging: bool = True
    log_directory: str = "logs"
    max_file_size_mb: int = 10
    backup_count: int = 5
    json_format: bool = False
    include_traceback: bool = True

@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    enable_terrain_modeling: bool = True
    terrain_resolution: float = 1.0  # meters per grid cell
    max_terrain_dimensions: Tuple[int, int] = (1000, 1000)  # grid cells
    enable_weather_effects: bool = True
    enable_time_of_day: bool = True
    enable_line_of_sight: bool = True

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_level: SecurityLevel = SecurityLevel.HIGH
    enable_rbac: bool = True
    default_role: str = "observer"
    require_authentication: bool = True

@dataclass
class SDKConfiguration:
    """Main SDK configuration"""
    network: NetworkConfig = field(default_factory=NetworkConfig)
    sensors: SensorConfig = field(default_factory=SensorConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    plugin_directories: List[str] = field(default_factory=lambda: ["plugins"])
    log_level: str = "INFO"
    enable_telemetry: bool = True
    max_concurrent_operations: int = 10
    timeout_seconds: float = 30.0
    
    @classmethod
    def from_file(cls, file_path: str) -> 'SDKConfiguration':
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Loaded configuration
            
        Raises:
            ConfigurationError: If the file cannot be loaded or parsed
        """
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
                
            # Create base configuration
            config = cls()
            
            # Update with file values
            if 'network' in config_dict:
                network_dict = config_dict['network']
                if 'encryption_level' in network_dict:
                    network_dict['encryption_level'] = SecurityLevel[network_dict['encryption_level']]
                config.network = NetworkConfig(**network_dict)
                
            if 'sensors' in config_dict:
                config.sensors = SensorConfig(**config_dict['sensors'])
                
            if 'ai' in config_dict:
                config.ai = AIConfig(**config_dict['ai'])
                
            # Update top-level fields
            for key in ['plugin_directories', 'log_level', 'enable_telemetry', 
                       'max_concurrent_operations', 'timeout_seconds']:
                if key in config_dict:
                    setattr(config, key, config_dict[key])
                    
            return config
            
        except (IOError, json.JSONDecodeError, KeyError) as e:
            raise ConfigurationError(f"Failed to load configuration from {file_path}: {e}")
    
    def to_file(self, file_path: str) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            file_path: Path to save the configuration file
            
        Raises:
            ConfigurationError: If the file cannot be saved
        """
        try:
            # Convert to dictionary
            config_dict = self.to_dict()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
        except (IOError, TypeError) as e:
            raise ConfigurationError(f"Failed to save configuration to {file_path}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        config_dict = asdict(self)
        
        # Convert enums to strings
        if 'network' in config_dict and 'encryption_level' in config_dict['network']:
            config_dict['network']['encryption_level'] = config_dict['network']['encryption_level'].name
            
        return config_dict
    
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Validate sensor update rate
        if self.sensors.update_rate <= 0:
            errors.append("Sensor update rate must be positive")
            
        # Validate AI decision time
        if self.ai.max_decision_time <= 0:
            errors.append("AI max decision time must be positive")
            
        # Validate timeout
        if self.timeout_seconds <= 0:
            errors.append("Timeout must be positive")
            
        # Validate concurrent operations
        if self.max_concurrent_operations <= 0:
            errors.append("Max concurrent operations must be positive")
            
        return errors