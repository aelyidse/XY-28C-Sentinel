"""
Utility decorators for XY-28C-Sentinel.
"""
import functools
import logging
import asyncio
from typing import Callable, Any, Optional
from .error_handler import ErrorHandler, SentinelError, ErrorCategory, ErrorSeverity

def handle_errors(component_id: Optional[str] = None):
    """
    Decorator to handle errors in methods.
    
    Args:
        component_id: ID of the component, defaults to the class name
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                # Get error handler from instance if available
                error_handler = getattr(self, 'error_handler', None)
                
                # Fall back to global error handler if not available
                if error_handler is None:
                    from ..system.system_controller import SystemController
                    system_controller = SystemController._instance
                    if system_controller:
                        error_handler = system_controller.error_handler
                
                # Use component ID from args or class name
                comp_id = component_id or self.__class__.__name__
                
                if error_handler:
                    handled = await error_handler.handle_error(e, comp_id)
                    if not handled and isinstance(e, Exception):
                        raise e
                else:
                    # Fall back to basic logging if no error handler is available
                    logger = logging.getLogger('sentinel')
                    logger.error(f"Error in {comp_id}.{func.__name__}: {e}")
                    raise e
                
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Log synchronously for non-async functions
                logger = logging.getLogger('sentinel')
                comp_id = component_id or self.__class__.__name__
                logger.error(f"Error in {comp_id}.{func.__name__}: {e}")
                raise e
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

def log_execution_time(logger_name: Optional[str] = None):
    """
    Decorator to log execution time of methods.
    
    Args:
        logger_name: Name of the logger to use
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            logger_to_use = logger_name or f"sentinel.{self.__class__.__name__}"
            logger = logging.getLogger(logger_to_use)
            
            start_time = asyncio.get_event_loop().time()
            try:
                result = await func(self, *args, **kwargs)
                execution_time = asyncio.get_event_loop().time() - start_time
                logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
                return result
            except Exception as e:
                execution_time = asyncio.get_event_loop().time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
                raise e
                
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            import time
            logger_to_use = logger_name or f"sentinel.{self.__class__.__name__}"
            logger = logging.getLogger(logger_to_use)
            
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
                raise e
                
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator