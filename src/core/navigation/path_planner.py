from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.spatial import KDTree
from sklearn.preprocessing import MinMaxScaler
from ..sensors.terrain.terrain_mapper import TerrainMapper
from ..physics.models.unified_environment import UnifiedEnvironment

class PathPlanner:
    def __init__(self, config: Dict[str, float]):
        self.resolution = config.get('resolution', 0.5)
        self.max_slope = config.get('max_slope', 30.0)  # degrees
        self.safety_margin = config.get('safety_margin', 2.0)  # meters
        self.terrain_mapper = TerrainMapper(resolution=self.resolution)
        self.weight_factors = {
            'distance': 0.3,
            'slope': 0.2,
            'roughness': 0.15,
            'exposure': 0.2,
            'obstacles': 0.15
        }
        
    def _adjust_cost_map_for_mission_phase(self, cost_map: np.ndarray, mission_phase: str) -> np.ndarray:
        if mission_phase == 'stealth':
            # Emphasize stealth by increasing cost for exposed areas
            cost_map += self._calculate_exposure_cost(self.terrain_data) * 2
        elif mission_phase == 'combat':
            # Prioritize proximity to target during combat phase
            cost_map += self._calculate_distance_cost(self.goal_point) * 1.5
        # Add more mission phases as needed
        return cost_map

    async def plan_path(
        self,
        start_point: np.ndarray,
        goal_point: np.ndarray,
        terrain_data: Dict[str, np.ndarray],
        obstacles: List[Dict[str, Any]],
        mission_phase: str
    ) -> Dict[str, Any]:
        # Create cost map
        cost_map = self._generate_cost_map(terrain_data, obstacles)
        cost_map = self._adjust_cost_map_for_mission_phase(cost_map, mission_phase)
        
        # Generate path using hybrid A* algorithm
        path = self._hybrid_astar_search(start_point, goal_point, cost_map, terrain_data)
        
        # Optimize path
        smoothed_path = self._optimize_path(path, cost_map)
        
        # Generate detailed waypoints
        waypoints = self._generate_waypoints(smoothed_path, terrain_data)
        
        return {
            'path': smoothed_path,
            'waypoints': waypoints,
            'cost_map': cost_map,
            'metrics': self._calculate_path_metrics(waypoints, terrain_data)
        }
        
    def _generate_cost_map(
        self,
        terrain_data: Dict[str, np.ndarray],
        obstacles: List[Dict[str, Any]]
    ) -> np.ndarray:
        # Initialize cost map
        cost_map = np.zeros_like(terrain_data['heights'])
        
        # Add terrain-based costs
        cost_map += self._calculate_slope_cost(terrain_data['slope'])
        cost_map += self._calculate_roughness_cost(terrain_data['roughness'])
        cost_map += self._calculate_exposure_cost(terrain_data)
        cost_map += self._calculate_clearance_cost(terrain_data['clearance'])
        dynamic_obstacles = terrain_data.get('dynamic_obstacles', [])
        predicted_obstacle_positions = self._predict_obstacle_positions(dynamic_obstacles, self.planning_horizon)
        cost_map += self._calculate_dynamic_obstacle_cost(predicted_obstacle_positions)
        return cost_map

    def _calculate_clearance_cost(self, clearance_map: np.ndarray) -> np.ndarray:
        # Calculate cost based on desired clearance
        desired_clearance = 10.0  # meters
        clearance_cost = np.abs(clearance_map - desired_clearance)
        return clearance_cost
        
        # Add obstacle costs
        cost_map += self._calculate_obstacle_cost(
            obstacles,
            cost_map.shape,
            terrain_data
        )
        
        # Normalize cost map
        scaler = MinMaxScaler()
        cost_map = scaler.fit_transform(cost_map)
        
        return cost_map
        
    def _hybrid_astar_search(
        self,
        start: np.ndarray,
        goal: np.ndarray,
        cost_map: np.ndarray,
        terrain_data: Dict[str, np.ndarray]
    ) -> List[np.ndarray]:
        class Node:
            def __init__(self, pos, g_cost, h_cost, parent=None):
                self.pos = pos
                self.g_cost = g_cost
                self.h_cost = h_cost
                self.f_cost = g_cost + h_cost
                self.parent = parent
                
        # Initialize search
        start_node = Node(
            start,
            0,
            self._heuristic_cost(start, goal)
        )
        open_set = {tuple(start): start_node}
        closed_set = set()
        
        while open_set:
            current = min(open_set.values(), key=lambda x: x.f_cost)
            current_pos = tuple(current.pos)
            
            if np.linalg.norm(current.pos - goal) < self.resolution:
                return self._reconstruct_path(current)
                
            open_set.pop(current_pos)
            closed_set.add(current_pos)
            
            # Generate successors
            for next_pos in self._get_neighbors(current.pos, cost_map):
                if tuple(next_pos) in closed_set:
                    continue
                    
                g_cost = current.g_cost + self._movement_cost(
                    current.pos,
                    next_pos,
                    cost_map,
                    terrain_data
                )
                h_cost = self._heuristic_cost(next_pos, goal)
                
                next_node = Node(next_pos, g_cost, h_cost, current)
                
                if tuple(next_pos) not in open_set or \
                   g_cost < open_set[tuple(next_pos)].g_cost:
                    open_set[tuple(next_pos)] = next_node
                    
        return None
        
    def _optimize_path(
        self,
        path: List[np.ndarray],
        cost_map: np.ndarray
    ) -> List[np.ndarray]:
        if not path:
            return path
            
        # Apply path smoothing
        smoothed = self._smooth_path(path)
        
        # Apply local optimization
        optimized = self._local_optimize(smoothed, cost_map)
        
        return optimized
        
    def _generate_waypoints(
        self,
        path: List[np.ndarray],
        terrain_data: Dict[str, np.ndarray]
    ) -> List[Dict[str, Any]]:
        waypoints = []
        
        for point in path:
            # Get terrain properties at point
            height = self._interpolate_height(point, terrain_data)
            slope = self._interpolate_value(point, terrain_data['slope'])
            
            waypoints.append({
                'position': point,
                'height': height,
                'slope': slope,
                'heading': self._calculate_heading(point, path),
                'constraints': self._get_point_constraints(point, terrain_data)
            })
            
        return waypoints

    def _predict_obstacle_positions(self, dynamic_obstacles: List[Dict[str, Any]], time_ahead: float) -> List[np.ndarray]:
        predicted_positions = []
        for obstacle in dynamic_obstacles:
            predicted_position = obstacle['position'] + obstacle['velocity'] * time_ahead
            predicted_positions.append(predicted_position)
        return predicted_positions

    def _calculate_dynamic_obstacle_cost(self, predicted_obstacle_positions: List[np.ndarray]) -> np.ndarray:
        # Calculate cost based on predicted obstacle positions
        cost = np.zeros_like(self.cost_map)
        for position in predicted_obstacle_positions:
            cost += self._gaussian_cost(position, sigma=5.0)
        return cost