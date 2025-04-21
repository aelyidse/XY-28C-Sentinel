from typing import Dict, List, Optional
import numpy as np
from scipy.interpolate import CubicSpline
from .path_planner import PathPlanner

class TrajectoryGenerator:
    def __init__(self, config: Dict[str, float]):
        self.max_velocity = config.get('max_velocity', 5.0)
        self.max_acceleration = config.get('max_acceleration', 2.0)
        self.max_jerk = config.get('max_jerk', 1.0)
        self.time_step = config.get('time_step', 0.1)
        
    def generate_trajectory(
        self,
        waypoints: List[Dict[str, Any]],
        terrain_data: Dict[str, np.ndarray],
        mission_phase: str
    ) -> Dict[str, np.ndarray]:
        # Extract waypoint positions
        positions = np.array([wp['position'] for wp in waypoints])
        
        # Generate time allocation
        times = self._allocate_time(positions, waypoints)
        
        # Generate smooth trajectory
        trajectory = self._generate_spline_trajectory(
            positions,
            times,
            waypoints
        )
        
        # Apply dynamic constraints
        constrained_trajectory = self._apply_dynamic_constraints(
            trajectory,
            terrain_data
        )
        
        return constrained_trajectory
        
    def _allocate_time(
        self,
        positions: np.ndarray,
        waypoints: List[Dict[str, Any]]
    ) -> np.ndarray:
        # Calculate distances between waypoints
        distances = np.linalg.norm(
            positions[1:] - positions[:-1],
            axis=1
        )
        
        # Adjust time based on terrain complexity
        complexity_factors = [
            self._calculate_complexity_factor(wp)
            for wp in waypoints[:-1]
        ]
        
        # Calculate time intervals
        intervals = distances / self.max_velocity * complexity_factors
        times = np.concatenate(([0], np.cumsum(intervals)))
        
        return times
    
    def _apply_dynamic_constraints(self, trajectory: Dict[str, np.ndarray], terrain_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        # Apply constraints based on terrain slope and roughness
        constrained_trajectory = trajectory.copy()
        for i, point in enumerate(trajectory['positions']):
            terrain_slope = self._interpolate_value(point, terrain_data['slope'])
            if terrain_slope > self.max_slope:
                # Adjust trajectory to maintain safe slope
                constrained_trajectory['positions'][i] += self._calculate_slope_adjustment(terrain_slope)
        constrained_trajectory = self._apply_mission_phase_constraints(trajectory, terrain_data, mission_phase)
        return constrained_trajectory

    def _apply_mission_phase_constraints(self, trajectory: Dict[str, np.ndarray], terrain_data: Dict[str, np.ndarray], mission_phase: str) -> Dict[str, np.ndarray]:
        if mission_phase == 'stealth':
            # Apply constraints to minimize detection risk
            constrained_trajectory = self._apply_stealth_constraints(trajectory, terrain_data)
        elif mission_phase == 'combat':
            # Apply constraints to optimize combat effectiveness
            constrained_trajectory = self._apply_combat_constraints(trajectory, terrain_data)
        # Add more mission phases as needed
        return constrained_trajectory