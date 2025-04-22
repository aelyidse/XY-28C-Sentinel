"""
Error handling module for XY-28C-Sentinel.

This module provides centralized error handling, classification, and recovery mechanisms.
"""
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Type
import traceback
import logging
import asyncio
from ..system.events import SystemEvent, SystemEventType

class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    SENSOR = "sensor"
    BLOCKCHAIN = "blockchain"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    UNKNOWN = "unknown"

class SentinelError(Exception):
    """Base exception class for XY-28C-Sentinel"""
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.timestamp = asyncio.get_event_loop().time()
        self.traceback = traceback.format_exc()

class ErrorHandler:
    """Centralized error handler for XY-28C-Sentinel"""
    
    def __init__(self, event_manager=None):
        self.logger = logging.getLogger('sentinel.error_handler')
        self.event_manager = event_manager
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {
            category: [] for category in ErrorCategory
        }
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        
    def register_handler(self, category: ErrorCategory, handler: Callable) -> None:
        """Register an error handler for a specific category"""
        self.error_handlers[category].append(handler)
        
    def register_recovery_strategy(self, exception_type: Type[Exception], strategy: Callable) -> None:
        """Register a recovery strategy for a specific exception type"""
        self.recovery_strategies[exception_type] = strategy
        
    async def handle_error(self, error: Exception, component_id: str = None) -> bool:
        """
        Handle an error and attempt recovery if possible
        
        Args:
            error: The exception to handle
            component_id: ID of the component that raised the error
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        # Convert to SentinelError if it's not already
        if not isinstance(error, SentinelError):
            if isinstance(error, (ConnectionError, TimeoutError)):
                sentinel_error = SentinelError(
                    str(error), 
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.ERROR
                )
            elif isinstance(error, (ValueError, TypeError, KeyError)):
                sentinel_error = SentinelError(
                    str(error), 
                    category=ErrorCategory.SOFTWARE,
                    severity=ErrorSeverity.WARNING
                )
            else:
                sentinel_error = SentinelError(
                    str(error), 
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.ERROR
                )
        else:
            sentinel_error = error
            
        # Log the error
        self._log_error(sentinel_error, component_id)
        
        # Publish error event if event manager is available
        if self.event_manager:
            await self.event_manager.publish(
                SystemEvent(
                    event_type=SystemEventType.ERROR,
                    component_id=component_id or "error_handler",
                    data={
                        "message": sentinel_error.message,
                        "category": sentinel_error.category.value,
                        "severity": sentinel_error.severity.value,
                        "details": sentinel_error.details,
                        "traceback": sentinel_error.traceback
                    },
                    priority=self._get_priority_from_severity(sentinel_error.severity)
                )
            )
        
        # Call specific handlers for this category
        for handler in self.error_handlers[sentinel_error.category]:
            try:
                await handler(sentinel_error)
            except Exception as e:
                self.logger.error(f"Error in error handler: {e}")
        
        # Attempt recovery if strategy exists
        error_type = type(error)
        if error_type in self.recovery_strategies:
            try:
                await self.recovery_strategies[error_type](error)
                return True
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
                
        return False
    
    def _log_error(self, error: SentinelError, component_id: Optional[str]) -> None:
        """Log error with appropriate severity"""
        log_message = f"[{component_id or 'unknown'}] {error.message}"
        
        if error.details:
            log_message += f" Details: {error.details}"
            
        if error.severity == ErrorSeverity.DEBUG:
            self.logger.debug(log_message)
        elif error.severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
    
    def _get_priority_from_severity(self, severity: ErrorSeverity) -> int:
        """Convert error severity to event priority"""
        if severity == ErrorSeverity.CRITICAL:
            return 0  # Highest priority
        elif severity == ErrorSeverity.ERROR:
            return 1
        elif severity == ErrorSeverity.WARNING:
            return 2
        else:
            return 3  # Lowest priority