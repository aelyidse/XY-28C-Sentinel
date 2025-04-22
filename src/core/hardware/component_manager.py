"""
Hardware Component Manager Module

This module provides a manager for hardware components.
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from .component import HardwareComponent, ComponentStatus
from .component_factory import ComponentFactory
from ..events.event_manager import EventManager
from ..system.events import SystemEvent, SystemEventType

class ComponentManager:
    """Manager for hardware components"""
    
    def __init__(self, event_manager: EventManager):
        self.logger = logging.getLogger("sentinel.hardware.manager")
        self.event_manager = event_manager
        self.components: Dict[str, HardwareComponent] = {}
        self._running = False
        
    async def initialize(self) -> bool:
        """Initialize the component manager and all components"""
        self.logger.info("Initializing hardware component manager")
        
        # Initialize all components
        init_tasks = []
        for component in self.components.values():
            init_tasks.append(component.initialize())
            
        # Wait for all components to initialize
        if init_tasks:
            results = await asyncio.gather(*init_tasks, return_exceptions=True)
            success = all(result is True for result in results if not isinstance(result, Exception))
        else:
            success = True
            
        self._running = success
        return success
        
    async def shutdown(self) -> None:
        """Shutdown the component manager and all components"""
        self.logger.info("Shutting down hardware component manager")
        self._running = False
        
        # Shutdown all components
        shutdown_tasks = []
        for component in self.components.values():
            shutdown_tasks.append(component.shutdown())
            
        # Wait for all components to shutdown
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            
    async def register_component(self, component: HardwareComponent) -> bool:
        """Register a hardware component"""
        if component.component_id in self.components:
            self.logger.warning(f"Component with ID {component.component_id} already registered")
            return False
            
        self.components[component.component_id] = component
        
        # Initialize component if manager is already running
        if self._running:
            await component.initialize()
            
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.COMPONENT_REGISTERED,
            component_id=component.component_id,
            data={"type": component.__class__.__name__}
        ))
        
        return True
        
    async def unregister_component(self, component_id: str) -> bool:
        """Unregister a hardware component"""
        if component_id not in self.components:
            self.logger.warning(f"Component with ID {component_id} not registered")
            return False
            
        component = self.components[component_id]
        
        # Shutdown component if it's running
        if component.status != ComponentStatus.OFFLINE:
            await component.shutdown()
            
        del self.components[component_id]
        
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.COMPONENT_UNREGISTERED,
            component_id=component_id,
            data={}
        ))
        
        return True
        
    def get_component(self, component_id: str) -> Optional[HardwareComponent]:
        """Get a component by ID"""
        return self.components.get(component_id)
        
    def get_components_by_type(self, component_type: type) -> List[HardwareComponent]:
        """Get all components of a specific type"""
        return [c for c in self.components.values() if isinstance(c, component_type)]
        
    async def create_component(self, component_type: str, component_id: str, config: Dict[str, Any] = None) -> Optional[HardwareComponent]:
        """Create and register a new component"""
        component = ComponentFactory.create_component(component_type, component_id, config)
        
        if component:
            success = await self.register_component(component)
            if success:
                return component
                
        return None
        
    async def update_components(self) -> None:
        """Update all components"""
        if not self._running:
            return
            
        update_tasks = []
        for component in self.components.values():
            update_tasks.append(component.update())
            
        await asyncio.gather(*update_tasks, return_exceptions=True)
        
    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all components"""
        health = {
            "total_components": len(self.components),
            "online_components": 0,
            "degraded_components": 0,
            "offline_components": 0,
            "error_components": 0,
            "components": {}
        }
        
        for component_id, component in self.components.items():
            status = await component.get_status()
            health["components"][component_id] = {
                "status": status.name,
                "type": component.__class__.__name__
            }
            
            if status == ComponentStatus.ONLINE:
                health["online_components"] += 1
            elif status == ComponentStatus.DEGRADED:
                health["degraded_components"] += 1
            elif status == ComponentStatus.OFFLINE:
                health["offline_components"] += 1
            elif status == ComponentStatus.ERROR:
                health["error_components"] += 1
                
        return health