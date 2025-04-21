from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
from ..physics.models.electronic_vulnerability import EMPVulnerabilityAnalyzer

class ThreatAnalyzer:
    def __init__(self):
        self.emp_analyzer = EMPVulnerabilityAnalyzer()
    
    def analyze_threat(self, threat_data: Dict) -> Dict:
        """Enhanced threat analysis with electronic vulnerability assessment"""
        analysis = {
            'severity_score': self._calculate_threat_severity(threat_data),
            'threat_type': self._determine_threat_type(threat_data),
            'predicted_trajectory': self._predict_threat_movement(threat_data),
            'exploitability_score': self._calculate_exploitability_score(threat_data),
            'electronic_vulnerability': self._assess_electronic_vulnerability(threat_data)
        }
        return analysis
        
    def _assess_electronic_vulnerability(self, threat_data: Dict) -> Dict:
        """Assess electronic system vulnerabilities of the threat"""
        if 'electronic_systems' not in threat_data:
            return {}
            
        vulnerability_scores = {}
        for system in threat_data['electronic_systems']:
            damage_analysis = self.emp_analyzer.compute_system_damage(
                system,
                threat_data.get('em_environment', {}),
                threat_data.get('exposure_time', 1.0)
            )
            vulnerability_scores[system.system_type.value] = damage_analysis
            
        return vulnerability_scores

    def _calculate_threat_severity(self, threat_data: Dict[str, Any]) -> float:
        """Calculate overall threat severity score."""
        # Simple implementation - replace with your scoring logic
        return np.mean([threat_data.get('signal_strength', 0), 
                       threat_data.get('range', 1000)])

    def _determine_threat_type(self, threat_data: Dict[str, Any]) -> str:
        """Determine threat type based on characteristics."""
        if threat_data.get('rf_signature') > 0.7:
            return 'radar_lock'
        if threat_data.get('laser_detection') > 0.5:
            return 'laser_guided'
        return 'generic_missile'

    def _predict_threat_movement(self, threat_data: Dict[str, Any]) -> np.ndarray:
        """Predict threat's future position."""
        # Simple extrapolation - replace with proper prediction model
        current_pos = np.array(threat_data.get('position', [0, 0, 0]))
        velocity = np.array(threat_data.get('velocity', [0, 0, 0]))
        predicted_pos = current_pos + velocity * 5  # Predict 5 seconds ahead
        
        return predicted_pos
        
    def _calculate_exploitability_score(self, threat_data: Dict[str, Any]) -> float:
        """Calculate how exploitable the threat is."""
        # Simple score based on detected vulnerabilities
        vulnerabilities = threat_data.get('detected_vulnerabilities', [])
        return min(len(vulnerabilities) / 10, 1.0)