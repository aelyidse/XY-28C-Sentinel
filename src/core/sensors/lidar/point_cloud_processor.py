from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy.spatial import KDTree
from sklearn.decomposition import PCA
from scipy.ndimage import gaussian_filter
from sklearn.cluster import DBSCAN
from ..fusion.sensor_fusion import SensorFusion
from ...physics.models.unified_environment import UnifiedEnvironment

class PointCloudProcessor:
    def __init__(self, config: Dict[str, float]):
        self.scan_rate = config['scan_rate']
        self.point_density = config['point_density']
        self.max_range = config['max_range']
        self.beam_divergence = config['beam_divergence']
        self.voxel_size = 0.1  # meters
        # Add advanced processing parameters
        self.adaptive_voxel_size = True
        self.voxel_cache = {}
        self.max_points_per_voxel = 1000
        self.edge_preservation = True
        self.intensity_based_filtering = True
        self.temporal_filtering = True
        self.motion_compensation = True
        self.kdtree = None
        self.ground_threshold = 0.3  # meters
        self.min_points_for_processing = 10
        self.max_cluster_size = 10000
        self.adaptive_ground_threshold = True
        self.noise_estimation_window = 50
        
    async def process_point_cloud(
        self,
        raw_points: np.ndarray,
        sensor_pose: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        # Remove noise and outliers
        filtered_points = self._filter_outliers(raw_points)
        
        # Ground plane segmentation
        ground_points, obstacle_points = self._segment_ground_plane(filtered_points)
        
        # Voxelize point cloud for efficiency
        voxelized_cloud = self._voxelize_point_cloud(obstacle_points)
        
        # Cluster detection
        clusters = self._detect_clusters(voxelized_cloud)
        
        # Feature extraction
        features = self._extract_features(clusters)
        
        return {
            'filtered_cloud': filtered_points,
            'ground_points': ground_points,
            'obstacle_points': obstacle_points,
            'clusters': clusters,
            'features': features
        }
        
    def _filter_outliers(
        self,
        points: np.ndarray,
        k_neighbors: int = 8,
        std_dev_threshold: float = 2.0
    ) -> np.ndarray:
        # Handle empty or very small point clouds
        if len(points) < self.min_points_for_processing:
            return points
            
        # Adaptive threshold based on point cloud density
        local_density = len(points) / np.prod(np.ptp(points, axis=0))
        adaptive_k = max(3, min(int(k_neighbors * np.log10(local_density)), 15))
        
        # Build KD-tree with error handling
        try:
            self.kdtree = KDTree(points)
        except ValueError as e:
            print(f"KDTree construction failed: {e}")
            return points
            
        # Calculate mean distances with outlier-robust statistics
        try:
            distances, _ = self.kdtree.query(points, k=adaptive_k)
            mean_distances = np.median(distances[:, 1:], axis=1)  # Use median instead of mean
            
            # MAD-based outlier detection (more robust than std dev)
            mad = np.median(np.abs(mean_distances - np.median(mean_distances)))
            threshold = np.median(mean_distances) + std_dev_threshold * mad * 1.4826
            mask = mean_distances < threshold
            
            return points[mask]
        except Exception as e:
            print(f"Distance calculation failed: {e}")
            return points

    def _segment_ground_plane(
        self,
        points: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        if len(points) < self.min_points_for_processing:
            return np.array([]), points
            
        # Adaptive ground threshold based on point cloud height range
        if self.adaptive_ground_threshold:
            height_range = np.ptp(points[:, 2])  # Z-axis range
            self.ground_threshold = max(0.1, min(height_range * 0.05, 0.5))
        
        # Enhanced RANSAC with early stopping and quality checks
        best_inliers = None
        best_inlier_count = 0
        best_normal = None
        min_required_inliers = max(len(points) * 0.1, self.min_points_for_processing)
        
        for iteration in range(100):
            try:
                # Randomly sample 3 non-collinear points
                sample_indices = np.random.choice(len(points), 3, replace=False)
                sample_points = points[sample_indices]
                
                # Check for collinearity
                v1 = sample_points[1] - sample_points[0]
                v2 = sample_points[2] - sample_points[0]
                normal = np.cross(v1, v2)
                normal_magnitude = np.linalg.norm(normal)
                
                if normal_magnitude < 1e-6:  # Points are collinear
                    continue
                    
                normal = normal / normal_magnitude
                d = -np.dot(normal, sample_points[0])
                
                # Find inliers with vectorized operations
                distances = np.abs(np.dot(points, normal) + d)
                inliers = distances < self.ground_threshold
                inlier_count = np.sum(inliers)
                
                if inlier_count > best_inlier_count:
                    best_inliers = inliers
                    best_inlier_count = inlier_count
                    best_normal = normal
                    
                    # Early stopping if we found a good enough plane
                    if inlier_count > len(points) * 0.8:
                        break
                        
            except Exception as e:
                print(f"RANSAC iteration failed: {e}")
                continue
                
        # Verify we found a valid ground plane
        if best_inlier_count < min_required_inliers or best_normal is None:
            return np.array([]), points
            
        ground_points = points[best_inliers]
        obstacle_points = points[~best_inliers]
        
        return ground_points, obstacle_points

    def _detect_clusters(
        self,
        points: np.ndarray,
        eps: float = 0.3,
        min_samples: int = 10
    ) -> List[np.ndarray]:
        if len(points) < min_samples:
            return []
            
        # Adaptive clustering parameters based on point cloud density
        local_density = len(points) / np.prod(np.ptp(points, axis=0))
        adaptive_eps = eps * np.sqrt(1.0 / local_density)
        adaptive_min_samples = max(3, min(int(min_samples * np.log10(local_density)), 20))
        
        try:
            clustering = DBSCAN(
                eps=adaptive_eps,
                min_samples=adaptive_min_samples,
                n_jobs=-1
            ).fit(points)
            
            # Handle clusters
            clusters = []
            unique_labels = np.unique(clustering.labels_)
            
            for label in unique_labels:
                if label != -1:  # Not noise
                    cluster_points = points[clustering.labels_ == label]
                    
                    # Filter out too large clusters (potential errors)
                    if len(cluster_points) <= self.max_cluster_size:
                        clusters.append(cluster_points)
                        
            return clusters
            
        except Exception as e:
            print(f"Clustering failed: {e}")
            return []
        
    def _extract_features(
        self,
        clusters: List[np.ndarray]
    ) -> List[Dict[str, float]]:
        features = []
        
        for cluster in clusters:
            # Calculate geometric features
            centroid = np.mean(cluster, axis=0)
            dimensions = np.max(cluster, axis=0) - np.min(cluster, axis=0)
            volume = np.prod(dimensions)
            density = len(cluster) / volume
            
            # Calculate statistical features
            covariance = np.cov(cluster.T)
            eigenvalues = np.linalg.eigvals(covariance)
            
            features.append({
                'centroid': centroid,
                'dimensions': dimensions,
                'volume': volume,
                'point_density': density,
                'eigenvalues': eigenvalues,
                'planarity': (eigenvalues[1] - eigenvalues[0]) / eigenvalues[2],
                'linearity': (eigenvalues[2] - eigenvalues[1]) / eigenvalues[2]
            })
            
        return features

    def _voxelize_point_cloud(
        self,
        points: np.ndarray,
        adaptive: bool = True
    ) -> np.ndarray:
        if len(points) < self.min_points_for_processing:
            return points
            
        if adaptive:
            # Calculate optimal voxel size based on point density
            point_density = len(points) / np.prod(np.ptp(points, axis=0))
            voxel_size = max(0.1, min(1.0, 1.0 / np.cbrt(point_density)))
        else:
            voxel_size = self.voxel_size
            
        # Use cached voxelization if available
        cache_key = self._generate_cache_key(points, voxel_size)
        if cache_key in self.voxel_cache:
            return self.voxel_cache[cache_key]
            
        voxelized = self._perform_voxelization(points, voxel_size)
        self.voxel_cache[cache_key] = voxelized
        return voxelized

    def process_point_cloud(self, points: np.ndarray) -> Dict[str, Any]:
        """
        Process raw point cloud data
        
        Args:
            points: Nx3 array of point cloud data (x, y, z coordinates)
            
        Returns:
            Dictionary containing processed data
        """
        self.point_cloud = points
        
        # Remove noise and outliers
        filtered_points = self._remove_outliers(points)
        
        # Ground segmentation
        self.ground_points, self.non_ground_points = self._segment_ground(filtered_points)
        
        # Generate terrain mesh
        self.terrain_mesh = self._generate_terrain_mesh(self.ground_points)
        
        return {
            'filtered_points': filtered_points,
            'ground_points': self.ground_points,
            'non_ground_points': self.non_ground_points,
            'terrain_mesh': self.terrain_mesh
        }
        
    def _remove_outliers(self, points: np.ndarray) -> np.ndarray:
        """Remove noise and outliers from point cloud"""
        # Build KD-tree for nearest neighbor search
        tree = KDTree(points)
        
        # Calculate point density
        distances, _ = tree.query(points, k=10)  # Find 10 nearest neighbors
        density = 1 / np.mean(distances, axis=1)
        
        # Remove points with low density (outliers)
        density_threshold = np.percentile(density, 5)
        return points[density > density_threshold]
        
    def _segment_ground(self, points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Segment ground points from non-ground points"""
        # Progressive Morphological Filter implementation
        cell_size = 1.0  # meters
        max_window_size = 20.0  # meters
        slope_threshold = 0.3  # radians
        
        # Create initial grid
        x_min, y_min = points[:, 0].min(), points[:, 1].min()
        x_max, y_max = points[:, 0].max(), points[:, 1].max()
        
        grid_size_x = int((x_max - x_min) / cell_size) + 1
        grid_size_y = int((y_max - y_min) / cell_size) + 1
        
        # Initialize elevation grid
        elevation_grid = np.full((grid_size_x, grid_size_y), np.nan)
        
        # Fill grid with minimum elevations
        for point in points:
            grid_x = int((point[0] - x_min) / cell_size)
            grid_y = int((point[1] - y_min) / cell_size)
            if np.isnan(elevation_grid[grid_x, grid_y]) or point[2] < elevation_grid[grid_x, grid_y]:
                elevation_grid[grid_x, grid_y] = point[2]
        
        # Progressive filtering
        window_size = 3
        while window_size <= max_window_size:
            # Apply morphological opening
            opened = gaussian_filter(elevation_grid, sigma=window_size/3)
            
            # Identify ground points
            diff = elevation_grid - opened
            ground_mask = diff < (slope_threshold * window_size * cell_size)
            
            # Update elevation grid
            elevation_grid[~ground_mask] = np.nan
            
            window_size *= 2
        
        # Classify points
        ground_indices = []
        non_ground_indices = []
        
        for i, point in enumerate(points):
            grid_x = int((point[0] - x_min) / cell_size)
            grid_y = int((point[1] - y_min) / cell_size)
            
            if not np.isnan(elevation_grid[grid_x, grid_y]):
                if abs(point[2] - elevation_grid[grid_x, grid_y]) < cell_size:
                    ground_indices.append(i)
                else:
                    non_ground_indices.append(i)
            else:
                non_ground_indices.append(i)
        
        return points[ground_indices], points[non_ground_indices]
        
    def _generate_terrain_mesh(self, ground_points: np.ndarray) -> Dict[str, np.ndarray]:
        """Generate terrain mesh from ground points"""
        # Create regular grid
        grid_size = 1.0  # meters
        x_min, y_min = ground_points[:, 0].min(), ground_points[:, 1].min()
        x_max, y_max = ground_points[:, 0].max(), ground_points[:, 1].max()
        
        x_grid = np.arange(x_min, x_max + grid_size, grid_size)
        y_grid = np.arange(y_min, y_max + grid_size, grid_size)
        
        # Initialize height grid
        height_grid = np.zeros((len(x_grid), len(y_grid)))
        weight_grid = np.zeros_like(height_grid)
        
        # Interpolate heights
        for point in ground_points:
            grid_x = int((point[0] - x_min) / grid_size)
            grid_y = int((point[1] - y_min) / grid_size)
            
            if 0 <= grid_x < len(x_grid) and 0 <= grid_y < len(y_grid):
                height_grid[grid_x, grid_y] += point[2]
                weight_grid[grid_x, grid_y] += 1
                
        # Average heights
        mask = weight_grid > 0
        height_grid[mask] /= weight_grid[mask]
        
        # Fill gaps using nearest neighbor interpolation
        from scipy.interpolate import NearestNDInterpolator
        x_indices, y_indices = np.nonzero(mask)
        interpolator = NearestNDInterpolator(
            list(zip(x_indices, y_indices)),
            height_grid[mask]
        )
        
        for i in range(len(x_grid)):
            for j in range(len(y_grid)):
                if not mask[i, j]:
                    height_grid[i, j] = interpolator(i, j)
        
        # Generate mesh vertices and faces
        vertices = []
        faces = []
        
        for i in range(len(x_grid)):
            for j in range(len(y_grid)):
                vertices.append([x_grid[i], y_grid[j], height_grid[i, j]])
                
                if i < len(x_grid) - 1 and j < len(y_grid) - 1:
                    v00 = i * len(y_grid) + j
                    v01 = i * len(y_grid) + (j + 1)
                    v10 = (i + 1) * len(y_grid) + j
                    v11 = (i + 1) * len(y_grid) + (j + 1)
                    
                    faces.extend([
                        [v00, v01, v10],
                        [v01, v11, v10]
                    ])
        
        return {
            'vertices': np.array(vertices),
            'faces': np.array(faces),
            'height_grid': height_grid,
            'grid_coordinates': (x_grid, y_grid)
        }