from typing import Dict, List, Tuple, Any
import numpy as np
from scipy.ndimage import gaussian_filter, sobel
from sklearn.cluster import DBSCAN

class TerrainAnalyzer:
    def __init__(self):
        self.terrain_mesh = None
        self.features = {}
        
    def analyze_terrain(self, terrain_data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Analyze terrain features from mesh data
        
        Args:
            terrain_data: Dictionary containing terrain mesh data
            
        Returns:
            Dictionary containing terrain analysis results
        """
        self.terrain_mesh = terrain_data
        
        # Calculate terrain metrics
        slope = self._calculate_slope()
        roughness = self._calculate_roughness()
        features = self._extract_terrain_features()
        
        return {
            'slope_map': slope,
            'roughness_map': roughness,
            'terrain_features': features,
            'statistics': self._calculate_statistics(slope, roughness)
        }
        
    def _calculate_slope(self) -> np.ndarray:
        """Calculate terrain slope"""
        height_grid = self.terrain_mesh['height_grid']
        
        # Calculate gradients
        dx = sobel(height_grid, axis=0)
        dy = sobel(height_grid, axis=1)
        
        # Calculate slope in degrees
        slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
        return slope
        
    def _calculate_roughness(self) -> np.ndarray:
        """Calculate terrain roughness"""
        height_grid = self.terrain_mesh['height_grid']
        
        # Apply Gaussian smoothing
        smoothed = gaussian_filter(height_grid, sigma=2.0)
        
        # Roughness as deviation from smoothed surface
        roughness = np.abs(height_grid - smoothed)
        return roughness
        
    def _extract_terrain_features(self) -> Dict[str, Any]:
        """Extract significant terrain features"""
        height_grid = self.terrain_mesh['height_grid']
        slope = self._calculate_slope()
        
        # Detect ridges and valleys
        ridges = self._detect_ridges(height_grid)
        valleys = self._detect_valleys(height_grid)
        
        # Detect flat areas
        flat_areas = slope < 5.0  # areas with slope less than 5 degrees
        
        # Cluster significant features
        features = self._cluster_features(ridges, valleys, flat_areas)
        
        return features
        
    def _detect_ridges(self, height_grid: np.ndarray) -> np.ndarray:
        """Detect ridge lines in terrain"""
        # Calculate curvature
        laplacian = gaussian_filter(height_grid, sigma=1.0, order=2)
        
        # Ridge points have negative curvature
        ridges = laplacian < -0.1
        return ridges
        
    def _detect_valleys(self, height_grid: np.ndarray) -> np.ndarray:
        """Detect valley lines in terrain"""
        # Calculate curvature
        laplacian = gaussian_filter(height_grid, sigma=1.0, order=2)
        
        # Valley points have positive curvature
        valleys = laplacian > 0.1
        return valleys
        
    def _cluster_features(
        self,
        ridges: np.ndarray,
        valleys: np.ndarray,
        flat_areas: np.ndarray
    ) -> Dict[str, List[np.ndarray]]:
        """Cluster terrain features into distinct regions"""
        features = {}
        
        # Convert boolean masks to point coordinates
        for feature_type, mask in [
            ('ridges', ridges),
            ('valleys', valleys),
            ('flat_areas', flat_areas)
        ]:
            points = np.column_stack(np.where(mask))
            
            if len(points) > 0:
                # Cluster points using DBSCAN
                clustering = DBSCAN(eps=3, min_samples=5).fit(points)
                
                # Collect clusters
                clusters = []
                for cluster_id in range(clustering.labels_.max() + 1):
                    cluster_points = points[clustering.labels_ == cluster_id]
                    clusters.append(cluster_points)
                    
                features[feature_type] = clusters
            else:
                features[feature_type] = []
                
        return features
        
    def _calculate_statistics(
        self,
        slope: np.ndarray,
        roughness: np.ndarray
    ) -> Dict[str, float]:
        """Calculate terrain statistics"""
        return {
            'mean_slope': np.mean(slope),
            'max_slope': np.max(slope),
            'mean_roughness': np.mean(roughness),
            'max_roughness': np.max(roughness),
            'elevation_range': np.ptp(self.terrain_mesh['height_grid']),
            'total_area': len(self.terrain_mesh['vertices'])
        }