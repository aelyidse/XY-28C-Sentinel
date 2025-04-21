from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.stats import entropy
from ..target_identification import TargetIdentifier
from ..spectral_analyzer import SpectralAnalyzer

class ConfidenceScorer:
    def __init__(self):
        self.base_weights = {
            'lidar': 0.35,
            'magnetic': 0.35,
            'spectral': 0.30
        }
        self.temporal_decay = 0.95
        self.min_confidence = 0.85
        self.history_window = 10
        # Add environmental impact factors
        self.environmental_weights = {
            'visibility': 0.3,
            'electromagnetic_noise': 0.3,
            'atmospheric_conditions': 0.4
        }
        
    def compute_fusion_confidence(
        self,
        sensor_confidences: Dict[str, float],
        temporal_history: List[Dict[str, float]],
        feature_matches: Dict[str, np.ndarray],
        environmental_conditions: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        # Calculate base confidence scores
        base_scores = self._compute_base_scores(sensor_confidences)
        
        # Apply temporal consistency
        temporal_scores = self._apply_temporal_consistency(
            base_scores,
            temporal_history
        )
        
        # Calculate feature consistency
        feature_scores = self._evaluate_feature_consistency(feature_matches)
        
        # Combine scores
        final_scores = self._combine_confidence_scores(
            temporal_scores,
            feature_scores
        )
        
        # Apply environmental adjustments
        if environmental_conditions:
            final_scores = self._adjust_for_environment(
                final_scores,
                environmental_conditions
            )
            
        return final_scores
        
    def _adjust_for_environment(
        self,
        scores: Dict[str, float],
        conditions: Dict[str, float]
    ) -> Dict[str, float]:
        adjusted_scores = scores.copy()
        
        # Adjust LiDAR confidence based on visibility
        if 'visibility' in conditions:
            visibility_factor = np.clip(conditions['visibility'] / 100.0, 0.3, 1.0)
            adjusted_scores['lidar'] *= visibility_factor
            
        # Adjust magnetic sensor confidence based on EM noise
        if 'electromagnetic_noise' in conditions:
            em_factor = 1.0 - np.clip(conditions['electromagnetic_noise'], 0.0, 0.7)
            adjusted_scores['magnetic'] *= em_factor
            
        # Adjust spectral confidence based on atmospheric conditions
        if 'atmospheric_clarity' in conditions:
            atm_factor = np.clip(conditions['atmospheric_clarity'], 0.4, 1.0)
            adjusted_scores['spectral'] *= atm_factor
            
        # Recalculate fusion confidence
        adjusted_scores['fusion'] = self._calculate_weighted_fusion(adjusted_scores)
        return adjusted_scores
        
    def _calculate_weighted_fusion(self, scores: Dict[str, float]) -> float:
        sensor_scores = [v for k, v in scores.items() if k != 'fusion']
        weights = [self.base_weights[k] for k in scores.keys() if k != 'fusion']
        return np.average(sensor_scores, weights=weights)
        
    def _compute_base_scores(
        self,
        sensor_confidences: Dict[str, float]
    ) -> Dict[str, float]:
        weighted_scores = {}
        
        for sensor, confidence in sensor_confidences.items():
            weight = self.base_weights.get(sensor, 0.1)
            reliability = self._assess_sensor_reliability(sensor, confidence)
            weighted_scores[sensor] = confidence * weight * reliability
            
        return weighted_scores
        
    def _apply_temporal_consistency(
        self,
        current_scores: Dict[str, float],
        history: List[Dict[str, float]]
    ) -> Dict[str, float]:
        if not history:
            return current_scores
            
        temporal_scores = {}
        for sensor, current_score in current_scores.items():
            historical_scores = [
                h.get(sensor, 0.0) for h in history[-self.history_window:]
            ]
            
            # Apply exponential decay to historical scores
            decay_factors = np.power(
                self.temporal_decay,
                np.arange(len(historical_scores))
            )
            weighted_history = np.sum(
                np.array(historical_scores) * decay_factors
            ) / np.sum(decay_factors)
            
            # Combine with current score
            temporal_scores[sensor] = 0.7 * current_score + 0.3 * weighted_history
            
        return temporal_scores
        
    def _evaluate_feature_consistency(
        self,
        feature_matches: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        feature_scores = {}
        
        for sensor, matches in feature_matches.items():
            # Calculate feature consistency score with temporal stability
            consistency = self._calculate_feature_consistency(matches)
            
            # Enhanced feature distinctiveness with spatial context
            distinctiveness = self._calculate_feature_distinctiveness(matches)
            
            # Add feature persistence score
            persistence = self._calculate_feature_persistence(matches)
            
            # Combine metrics with weighted average
            feature_scores[sensor] = np.average(
                [consistency, distinctiveness, persistence],
                weights=[0.4, 0.3, 0.3]
            )
            
        return feature_scores
        
    def _calculate_feature_persistence(
        self,
        matches: np.ndarray
    ) -> float:
        if len(matches) < 2:
            return 0.0
            
        # Calculate temporal stability of features
        temporal_stability = np.mean(
            np.abs(np.diff(matches, axis=0)),
            axis=0
        )
        
        # Convert to persistence score
        persistence_score = 1.0 / (1.0 + np.mean(temporal_stability))
        return np.clip(persistence_score, 0.0, 1.0)
        
    def _calculate_feature_consistency(
        self,
        matches: np.ndarray
    ) -> float:
        if len(matches) < 2:
            return 0.0
            
        # Calculate variance in feature matches
        match_variance = np.var(matches, axis=0)
        consistency_score = 1.0 / (1.0 + np.mean(match_variance))
        
        return np.clip(consistency_score, 0.0, 1.0)
        
    def _calculate_feature_distinctiveness(
        self,
        matches: np.ndarray
    ) -> float:
        if len(matches) < 2:
            return 0.0
            
        # Calculate entropy of feature distributions
        feature_distributions = np.histogram(
            matches,
            bins=10,
            density=True
        )[0]
        
        distinctiveness = entropy(feature_distributions + 1e-10)
        return np.clip(1.0 - distinctiveness/np.log(10), 0.0, 1.0)
        
    def _assess_sensor_reliability(
        self,
        sensor: str,
        confidence: float
    ) -> float:
        # Base reliability factors
        reliability_factors = {
            'lidar': 0.95,
            'magnetic': 0.90,
            'spectral': 0.85
        }
        
        base_reliability = reliability_factors.get(sensor, 0.80)
        
        # Adjust based on confidence
        if confidence < self.min_confidence:
            reliability_penalty = ((self.min_confidence - confidence) / 
                                 self.min_confidence) ** 2
            base_reliability *= (1.0 - reliability_penalty)
            
        return base_reliability
        
    def _combine_confidence_scores(
        self,
        temporal_scores: Dict[str, float],
        feature_scores: Dict[str, float]
    ) -> Dict[str, float]:
        combined_scores = {}
        
        for sensor in temporal_scores.keys():
            temporal_weight = 0.6
            feature_weight = 0.4
            
            combined_scores[sensor] = (
                temporal_weight * temporal_scores[sensor] +
                feature_weight * feature_scores.get(sensor, 0.0)
            )
            
        # Add overall fusion confidence
        combined_scores['fusion'] = np.mean(list(combined_scores.values()))
        
        return combined_scores