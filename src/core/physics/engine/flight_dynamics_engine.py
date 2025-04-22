from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import logging
from ...components.component_interface import Component

class FlightDynamicsEngine(Component):
    """
    Physics engine component for accurate flight dynamics simulation.
    
    This component provides high-fidelity flight dynamics simulation capabilities
    including aerodynamics, propulsion, and environmental effects.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}
        self._initialized = False
        
        # Flight dynamics state
        self._position = np.zeros(3)  # x, y, z in meters
        self._velocity = np.zeros(3)  # vx, vy, vz in m/s
        self._acceleration = np.zeros(3)  # ax, ay, az in m/s²
        self._orientation = np.zeros(4)  # quaternion (w, x, y, z)
        self._angular_velocity = np.zeros(3)  # wx, wy, wz in rad/s
        
        # Physics parameters
        self._mass = 0.0  # kg
        self._inertia_tensor = np.zeros((3, 3))  # kg·m²
        self._drag_coefficient = 0.0
        self._lift_coefficient = 0.0
        self._thrust = 0.0  # N
        
        # Environment parameters
        self._air_density = 1.225  # kg/m³ (sea level)
        self._gravity = np.array([0, 0, -9.81])  # m/s²
        self._wind_velocity = np.zeros(3)  # m/s
        
    async def initialize(self) -> None:
        """Initialize the flight dynamics engine"""
        self.logger.info("Initializing flight dynamics engine")
        
        # Load default configuration
        self._config = {
            "time_step": 0.01,  # seconds
            "simulation_rate": 100,  # Hz
            "accuracy_level": "high",
            "enable_atmospheric_model": True,
            "enable_wind_model": True,
            "enable_turbulence": True
        }
        
        # Initialize physics parameters
        self._mass = 120.0  # kg
        self._inertia_tensor = np.array([
            [25.0, 0.0, 0.0],
            [0.0, 25.0, 0.0],
            [0.0, 0.0, 10.0]
        ])
        self._drag_coefficient = 0.3
        self._lift_coefficient = 1.2
        
        self._initialized = True
        self.logger.info("Flight dynamics engine initialized successfully")
    
    async def shutdown(self) -> None:
        """Clean up resources when shutting down"""
        self.logger.info("Shutting down flight dynamics engine")
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
            "status": "active" if self._initialized else "inactive"
        }
    
    def get_services(self) -> List[str]:
        """Get the services provided by this component"""
        return [
            "flight_dynamics_simulation",
            "aerodynamics_calculation",
            "trajectory_prediction",
            "stability_analysis"
        ]
    
    async def update(self, delta_time: float) -> None:
        """
        Update the flight dynamics simulation
        
        Args:
            delta_time: Time step in seconds
        """
        if not self._initialized:
            return
            
        # Calculate forces
        gravity_force = self._mass * self._gravity
        drag_force = self._calculate_drag_force()
        lift_force = self._calculate_lift_force()
        thrust_force = self._calculate_thrust_force()
        
        # Sum all forces
        total_force = gravity_force + drag_force + lift_force + thrust_force
        
        # Calculate acceleration (F = ma)
        self._acceleration = total_force / self._mass
        
        # Update velocity (v = v0 + at)
        self._velocity += self._acceleration * delta_time
        
        # Update position (p = p0 + vt)
        self._position += self._velocity * delta_time
        
        # Update orientation and angular velocity
        self._update_orientation(delta_time)
    
    def _calculate_drag_force(self) -> np.ndarray:
        """Calculate aerodynamic drag force"""
        velocity_squared = np.sum(self._velocity ** 2)
        if velocity_squared < 1e-6:
            return np.zeros(3)
            
        velocity_unit = self._velocity / np.sqrt(velocity_squared)
        drag_magnitude = 0.5 * self._air_density * velocity_squared * self._drag_coefficient
        
        return -drag_magnitude * velocity_unit
    
    def _calculate_lift_force(self) -> np.ndarray:
        """Calculate aerodynamic lift force"""
        velocity_squared = np.sum(self._velocity ** 2)
        if velocity_squared < 1e-6:
            return np.zeros(3)
            
        # Calculate lift direction (perpendicular to velocity and body up vector)
        velocity_unit = self._velocity / np.sqrt(velocity_squared)
        body_up = self._quaternion_rotate(np.array([0, 0, 1]))
        lift_direction = np.cross(velocity_unit, np.cross(body_up, velocity_unit))
        
        # Normalize lift direction
        lift_direction_norm = np.linalg.norm(lift_direction)
        if lift_direction_norm < 1e-6:
            return np.zeros(3)
            
        lift_direction = lift_direction / lift_direction_norm
        
        # Calculate lift magnitude
        lift_magnitude = 0.5 * self._air_density * velocity_squared * self._lift_coefficient
        
        return lift_magnitude * lift_direction
    
    def _calculate_thrust_force(self) -> np.ndarray:
        """Calculate propulsion thrust force"""
        # Thrust is applied in the body forward direction
        body_forward = self._quaternion_rotate(np.array([1, 0, 0]))
        return self._thrust * body_forward
    
    def _update_orientation(self, delta_time: float) -> None:
        """Update orientation based on angular velocity"""
        # Convert angular velocity to quaternion rate
        w, x, y, z = self._orientation
        wx, wy, wz = self._angular_velocity
        
        q_dot = 0.5 * np.array([
            -x*wx - y*wy - z*wz,
            w*wx + y*wz - z*wy,
            w*wy + z*wx - x*wz,
            w*wz + x*wy - y*wx
        ])
        
        # Update quaternion
        self._orientation += q_dot * delta_time
        
        # Normalize quaternion
        self._orientation = self._orientation / np.linalg.norm(self._orientation)
    
    def _quaternion_rotate(self, vector: np.ndarray) -> np.ndarray:
        """Rotate a vector by the current orientation quaternion"""
        w, x, y, z = self._orientation
        
        # Quaternion rotation formula: q * v * q^-1
        # Simplified implementation
        t = 2.0 * (y*vector[2] - z*vector[1])
        u = 2.0 * (z*vector[0] - x*vector[2])
        v = 2.0 * (x*vector[1] - y*vector[0])
        
        return np.array([
            vector[0] + w*t + y*v - z*u,
            vector[1] + w*u + z*t - x*v,
            vector[2] + w*v + x*u - y*t
        ])
    
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
        self._mass = mass
        self._inertia_tensor = inertia
        self._drag_coefficient = drag_coef
        self._lift_coefficient = lift_coef
    
    def set_thrust(self, thrust: float) -> None:
        """
        Set engine thrust
        
        Args:
            thrust: Thrust force in Newtons
        """
        self._thrust = thrust
    
    def set_environment(self, air_density: float, gravity: np.ndarray, 
                       wind: np.ndarray) -> None:
        """
        Set environmental parameters
        
        Args:
            air_density: Air density in kg/m³
            gravity: Gravity vector in m/s²
            wind: Wind velocity vector in m/s
        """
        self._air_density = air_density
        self._gravity = gravity
        self._wind_velocity = wind
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current flight dynamics state
        
        Returns:
            Dictionary containing position, velocity, acceleration, orientation
        """
        return {
            "position": self._position.copy(),
            "velocity": self._velocity.copy(),
            "acceleration": self._acceleration.copy(),
            "orientation": self._orientation.copy(),
            "angular_velocity": self._angular_velocity.copy()
        }
    
    def set_state(self, position: np.ndarray = None, velocity: np.ndarray = None,
                 orientation: np.ndarray = None, angular_velocity: np.ndarray = None) -> None:
        """
        Set the flight dynamics state
        
        Args:
            position: Position vector (x, y, z) in meters
            velocity: Velocity vector (vx, vy, vz) in m/s
            orientation: Orientation quaternion (w, x, y, z)
            angular_velocity: Angular velocity vector (wx, wy, wz) in rad/s
        """
        if position is not None:
            self._position = position.copy()
        
        if velocity is not None:
            self._velocity = velocity.copy()
        
        if orientation is not None:
            self._orientation = orientation.copy()
            # Normalize quaternion
            self._orientation = self._orientation / np.linalg.norm(self._orientation)
        
        if angular_velocity is not None:
            self._angular_velocity = angular_velocity.copy()