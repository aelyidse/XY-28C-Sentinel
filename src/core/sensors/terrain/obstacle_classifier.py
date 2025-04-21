from typing import Dict, List, Tuple
import numpy as np
from enum import Enum

class ObstacleType(Enum):
    BUILDING = "building"
    VEGETATION = "vegetation"
    VEHICLE = "vehicle"
    POWER_LINE = "power_line"
    TOWER = "tower"
    UNKNOWN = "unknown"

class ObstacleClassifier:
    def __init__(self):
        self.min_confidence = 0.85
        self.feature_weights = {
            'dimensions': 0.4,
            'density': 0.3,
            'geometry': 0.3
        }
        
    def classify_obstacle(
        self,
        points: np.ndarray,
        features: Dict[str, float]
    ) -> Tuple[ObstacleType, float]:
        # Extract geometric features
        geometric_features = self._extract_geometric_features(points)
        
        # Calculate feature scores
        scores = {}
        for obstacle_type in ObstacleType:
            if obstacle_type != ObstacleType.UNKNOWN:
                scores[obstacle_type] = self._calculate_type_score(
                    geometric_features,
                    features,
                    obstacle_type
                )
                
        # Select best match
        best_type = max(scores.items(), key=lambda x: x[1])
        
        if best_type[1] >= self.min_confidence:
            return best_type[0], best_type[1]
        return ObstacleType.UNKNOWN, best_type[1]
        
    def _extract_geometric_features(
        self,
        points: np.ndarray
    ) -> Dict[str, float]:
        # Calculate basic geometric properties
        dimensions = np.max(points, axis=0) - np.min(points, axis=0)
        volume = np.prod(dimensions)
        density = len(points) / volume
        
        # Calculate shape features
        pca = PCA(n_components=3)
        pca.fit(points)
        
        return {
            'dimensions': dimensions,
            'volume': volume,
            'density': density,
            'linearity': pca.explained_variance_ratio_[0],
            'planarity': pca.explained_variance_ratio_[1],
            'sphericity': pca.explained_variance_ratio_[2]
        }