from typing import Dict, Any, List, Optional
import logging
import numpy as np
from ...components.component_interface import Component
from .flight_dynamics_engine import FlightDynamicsEngine

class PhysicsEngineComponent(Component):
    """
    Physics engine integration component for the XY-28C-Sentinel system.
    
    This component integrates various physics simulation capabilities including
    flight dynamics, environmental effects, and sensor simulation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}
        self._initialized = False
        
        # Physics engines
        self.flight_dynamics = FlightDynamicsEngine()
        
        # Simulation parameters
        self._time_step = 0.01  # seconds
        self._simulation_time = 0.0  # seconds
        self._paused = True
    
    async def initialize(self) -> None:
        """Initialize the physics engine component"""
        self.logger.info("Initializing physics engine component")
        
        # Initialize flight dynamics engine
        await self.flight_dynamics.initialize()
        
        # Load default configuration
        self._config = {
            "time_step": 0.01,  # seconds
            "max_simulation_rate": 1000,  # Hz
            "real_time_factor": 1.0,
            "enable_environmental_effects": True
        }
        
        self._initialized = True
        self._paused = False
        self.logger.info("Physics engine component initialized successfully")
    
    async def shutdown(self) -> None:
        """Clean up resources when shutting down"""
        self.logger.info("Shutting down physics engine component")
        
        # Shutdown flight dynamics engine
        await self.flight_dynamics.shutdown()
        
        self._initialized = False
    
    def get_component_type(self) -> str:
        """Get the type of this component"""
        return "physics_engine"
    
    def get_component_info(self) -> Dict[str, Any]:
        """Get information about this component"""
        return {
            "type": self.get_component_type(),
            "services": self.get_services(),
            "config": self._config,
            "status": "active" if self._initialized else "inactive",
            "simulation_time": self._simulation_time,
            "paused": self._paused
        }
    
    def get_services(self) -> List[str]:
        """Get the services provided by this component"""
        return [
            "physics_simulation",
            "flight_dynamics",
            "environmental_simulation",
            "sensor_physics"
        ]
    
    async def update(self, delta_time: Optional[float] = None) -> None:
        """
        Update the physics simulation
        
        Args:
            delta_time: Optional time step override in seconds
        """
        if not self._initialized or self._paused:
            return
            
        # Use provided delta time or default time step
        dt = delta_time if delta_time is not None else self._time_step
        
        # Update flight dynamics
        await self.flight_dynamics.update(dt)
        
        # Update simulation time
        self._simulation_time += dt
    
    def set_time_step(self, time_step: float) -> None:
        """
        Set the simulation time step
        
        Args:
            time_step: Time step in seconds
        """
        if time_step > 0:
            self._time_step = time_step
            self._config["time_step"] = time_step
    
    def pause_simulation(self) -> None:
        """Pause the physics simulation"""
        self._paused = True
    
    def resume_simulation(self) -> None:
        """Resume the physics simulation"""
        self._paused = False
    
    def reset_simulation(self) -> None:
        """Reset the physics simulation to initial state"""
        self._simulation_time = 0.0
        
        # Reset flight dynamics to initial state
        self.flight_dynamics.set_state(
            position=np.zeros(3),
            velocity=np.zeros(3),
            orientation=np.array([1.0, 0.0, 0.0, 0.0]),  # Identity quaternion
            angular_velocity=np.zeros(3)
        )
    
    def get_flight_state(self) -> Dict[str, Any]:
        """
        Get the current flight state
        
        Returns:
            Dictionary containing flight dynamics state
        """
        return self.flight_dynamics.get_state()
    
    def set_aircraft_parameters(self, mass: float, inertia: np.ndarray, 
                               drag_coef: float, lift_coef: float) -> None:
        """
        Set aircraft physical parameters
        
        Args:
            mass: Aircraft mass in kg
            inertia: 3x3 inertia tensor in kg·m²
            drag_coef: Drag coefficient
            lift_coef: Lift coefficient
        """
        self.flight_dynamics.set_aircraft_parameters(mass, inertia, drag_coef, lift_coef)
    
    def set_environmental_conditions(self, altitude: float, temperature: float, 
                                    wind_speed: float, wind_direction: float) -> None:
        """
        Set environmental conditions
        
        Args:
            altitude: Altitude in meters
            temperature: Temperature in Kelvin
            wind_speed: Wind speed in m/s
            wind_direction: Wind direction in radians (0 = North, π/2 = East)
        """
        # Calculate air density based on altitude and temperature
        # Simple atmospheric model (exponential decay)
        air_density = 1.225 * np.exp(-altitude / 8500.0)
        
        # Calculate wind vector
        wind_x = wind_speed * np.sin(wind_direction)
        wind_y = wind_speed * np.cos(wind_direction)
        wind = np.array([wind_x, wind_y, 0.0])
        
        # Standard gravity
        gravity = np.array([0.0, 0.0, -9.81])
        
        # Update flight dynamics environment
        self.flight_dynamics.set_environment(air_density, gravity, wind)