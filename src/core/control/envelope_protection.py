import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class FlightEnvelope:
    max_mach: float
    min_mach: float
    max_altitude: float
    min_altitude: float
    max_angle_of_attack: float
    max_sideslip: float
    max_g_load: float
    max_roll_rate: float
    max_pitch_rate: float
    max_yaw_rate: float

class EnvelopeProtectionSystem:
    def __init__(self, envelope: FlightEnvelope):
        self.envelope = envelope
        self.safety_margins = {
            'angle_of_attack': 0.8,
            'g_load': 0.85,
            'mach': 0.9
        }
        
    async def check_envelope_violations(
        self,
        state: Dict[str, np.ndarray],
        predicted_state: Dict[str, np.ndarray]
    ) -> Dict[str, Tuple[bool, float]]:
        """Check for current and predicted envelope violations"""
        violations = {}
        
        # Current state checks
        velocity = np.linalg.norm(state['velocity'])
        mach = velocity / 343.0
        alpha = np.arctan2(state['velocity'][2], state['velocity'][0])
        beta = np.arcsin(state['velocity'][1]/velocity)
        
        violations.update({
            'mach': self._check_mach(mach),
            'altitude': self._check_altitude(state['position'][2]),
            'angle_of_attack': self._check_angle_of_attack(alpha),
            'sideslip': self._check_sideslip(beta),
            'g_load': self._check_g_load(state['angular_velocity'])
        })
        
        # Predicted state checks (if provided)
        if predicted_state:
            p_velocity = np.linalg.norm(predicted_state['velocity'])
            p_mach = p_velocity / 343.0
            p_alpha = np.arctan2(predicted_state['velocity'][2], predicted_state['velocity'][0])
            
            violations.update({
                'predicted_mach': self._check_mach(p_mach),
                'predicted_angle_of_attack': self._check_angle_of_attack(p_alpha)
            })
            
        return violations
        
    def _check_mach(self, mach: float) -> Tuple[bool, float]:
        """Check mach number limits"""
        violation = mach > self.envelope.max_mach * self.safety_margins['mach']
        severity = max(0, (mach - self.envelope.max_mach * self.safety_margins['mach']) / 
                      (self.envelope.max_mach - self.envelope.max_mach * self.safety_margins['mach']))
        return (violation, severity)
        
    def _check_angle_of_attack(self, alpha: float) -> Tuple[bool, float]:
        """Check angle of attack limits"""
        violation = abs(alpha) > self.envelope.max_angle_of_attack * self.safety_margins['angle_of_attack']
        severity = max(0, (abs(alpha) - self.envelope.max_angle_of_attack * self.safety_margins['angle_of_attack']) / 
                         (self.envelope.max_angle_of_attack - self.envelope.max_angle_of_attack * self.safety_margins['angle_of_attack']))
        return (violation, severity)
        
    def _check_g_load(self, angular_velocity: np.ndarray) -> Tuple[bool, float]:
        """Check g-load limits"""
        g_load = np.linalg.norm(angular_velocity)**2 / 9.81
        violation = g_load > self.envelope.max_g_load * self.safety_margins['g_load']
        severity = max(0, (g_load - self.envelope.max_g_load * self.safety_margins['g_load']) / 
                      (self.envelope.max_g_load - self.envelope.max_g_load * self.safety_margins['g_load']))
        return (violation, severity)
        
    async def predict_state(
        self,
        current_state: Dict[str, np.ndarray],
        time_horizon: float
    ) -> Dict[str, np.ndarray]:
        """Predict state at future time using simplified dynamics"""
        predicted_state = {}
        
        # Simple linear prediction
        predicted_state['position'] = current_state['position'] + current_state['velocity'] * time_horizon
        
        # Account for gravity in velocity prediction
        predicted_velocity = current_state['velocity'].copy()
        predicted_velocity[2] -= 9.81 * time_horizon  # Simple gravity effect
        
        predicted_state['velocity'] = predicted_velocity
        
        # Angular rates assumed constant for short prediction horizon
        predicted_state['angular_velocity'] = current_state['angular_velocity']
        
        return predicted_state