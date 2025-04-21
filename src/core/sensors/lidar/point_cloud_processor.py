from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.spatial import KDTree
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