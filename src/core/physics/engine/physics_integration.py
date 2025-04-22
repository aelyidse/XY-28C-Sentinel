import asyncio
import logging
from typing import Dict, Any
import numpy as np
from ...components.component_system import ComponentSystem
from .physics_engine_component import PhysicsEngineComponent

class PhysicsIntegration:
    """
    Integration utilities for the physics engine with the component system.
    """
    
    @staticmethod
    async def register_physics_components(component_system: ComponentSystem) -> Dict[str, str]:
        """
        Register physics components with the component system
        
        Args:
            component_system: The component system to register with
            
        Returns:
            Dictionary of registered component IDs
        """
        logger = logging.getLogger(__name__)
        logger.info("Registering physics components")
        
        registered_components = {}
        
        # Register physics engine component
        physics_engine_id = await component_system.load_component(
            PhysicsEngineComponent,
            "physics_engine"
        )
        
        if physics_engine_id:
            registered_components["physics_engine"] = physics_engine_id
            logger.info(f"Registered physics engine component with ID: {physics_engine_id}")
        else:
            logger.error("Failed to register physics engine component")
        
        return registered_components
    
    @staticmethod
    async def run_simulation_test(component_system: ComponentSystem, duration: float = 10.0) -> None:
        """
        Run a simple physics simulation test
        
        Args:
            component_system: The component system containing physics components
            duration: Simulation duration in seconds
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Running physics simulation test for {duration} seconds")
        
        # Get physics engine component
        physics_engine = component_system.get_component("physics_engine")
        if not physics_engine:
            logger.error("Physics engine component not found")
            return
        
        # Set aircraft parameters
        inertia = np.array([
            [25.0, 0.0, 0.0],
            [0.0, 25.0, 0.0],
            [0.0, 0.0, 10.0]
        ])
        physics_engine.set_aircraft_parameters(120.0, inertia, 0.3, 1.2)
        
        # Set environmental conditions
        physics_engine.set_environmental_conditions(0.0, 288.15, 5.0, 0.0)
        
        # Set initial state
        physics_engine.flight_dynamics.set_state(
            position=np.array([0.0, 0.0, 100.0]),  # 100m altitude
            velocity=np.array([50.0, 0.0, 0.0]),   # 50 m/s forward
            orientation=np.array([1.0, 0.0, 0.0, 0.0])  # Level flight
        )
        
        # Set thrust
        physics_engine.flight_dynamics.set_thrust(1200.0)  # 1200N thrust
        
        # Run simulation
        time_step = 0.01
        steps = int(duration / time_step)
        
        for i in range(steps):
            await physics_engine.update(time_step)
            
            # Log state every second
            if i % 100 == 0:
                state = physics_engine.get_flight_state()
                logger.info(f"Time: {i * time_step:.2f}s, Position: {state['position']}, "
                           f"Velocity: {state['velocity']}")
        
        # Final state
        final_state = physics_engine.get_flight_state()
        logger.info(f"Final position: {final_state['position']}")
        logger.info(f"Final velocity: {final_state['velocity']}")