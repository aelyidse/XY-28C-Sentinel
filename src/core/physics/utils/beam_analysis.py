import numpy as np
from typing import Dict

class BeamAnalyzer:
    @staticmethod
    def calculate_beam_parameters(field: np.ndarray) -> Dict[str, float]:
        """Calculate beam width, divergence, and peak intensity"""
        magnitude = np.abs(field)
        peak_idx = np.unravel_index(np.argmax(magnitude), magnitude.shape)
        peak_intensity = magnitude[peak_idx]
        
        # Calculate -3dB beam width
        half_power = peak_intensity * 0.707
        beam_width = np.sum(magnitude > half_power) / magnitude.size
        
        return {
            'peak_intensity': peak_intensity,
            'beam_width': beam_width,
            'divergence': BeamAnalyzer._calculate_divergence(magnitude),
            'focus_quality': BeamAnalyzer._calculate_focus_quality(magnitude)
        }
        
    @staticmethod
    def _calculate_divergence(magnitude: np.ndarray) -> float:
        """Calculate beam divergence angle"""
        # Implementation depends on coordinate system
        return np.std(magnitude) / np.mean(magnitude)
        
    @staticmethod
    def _calculate_focus_quality(magnitude: np.ndarray) -> float:
        """Calculate focus quality metric (0-1)"""
        peak = np.max(magnitude)
        mean = np.mean(magnitude)
        return (peak - mean) / peak