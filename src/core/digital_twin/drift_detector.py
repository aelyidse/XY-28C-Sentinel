import numpy as np
from typing import Dict

class DriftDetector:
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self._drift_history = []
        
    def check_drift(self, physical_state: Dict, digital_state: Dict) -> bool:
        """Check for significant drift between physical and digital states"""
        position_diff = np.linalg.norm(
            np.array(physical_state['position']) - 
            np.array(digital_state['position'])
        )
        
        orientation_diff = np.arccos(
            np.dot(
                physical_state['orientation'],
                digital_state['orientation']
            )
        )
        
        total_diff = position_diff + orientation_diff
        self._drift_history.append(total_diff)
        
        if len(self._drift_history) > 10:
            avg_diff = np.mean(self._drift_history[-10:])
            return avg_diff > self.threshold
            
        return False
        
    def calculate_correction(self, physical_state: Dict, digital_state: Dict) -> Dict:
        """Calculate correction to minimize drift"""
        return {
            'position_correction': np.array(physical_state['position']) - 
                                  np.array(digital_state['position']),
            'orientation_correction': self._quaternion_diff(
                physical_state['orientation'],
                digital_state['orientation']
            )
        }
        
    def _quaternion_diff(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """Calculate quaternion difference"""
        return np.array([
            q1[0]*q2[0] + q1[1]*q2[1] + q1[2]*q2[2] + q1[3]*q2[3],
            q1[0]*q2[1] - q1[1]*q2[0] - q1[2]*q2[3] + q1[3]*q2[2],
            q1[0]*q2[2] + q1[1]*q2[3] - q1[2]*q2[0] - q1[3]*q2[1],
            q1[0]*q2[3] - q1[1]*q2[2] + q1[2]*q2[1] - q1[3]*q2[0]
        ])