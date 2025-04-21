import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class StabilityLimits:
    max_angle_of_attack: float  # radians
    max_sideslip: float  # radians
    max_roll_rate: float  # rad/s
    max_pitch_rate: float  # rad/s
    max_yaw_rate: float  # rad/s

class StabilityAugmentationSystem:
    def __init__(self, limits: StabilityLimits):
        self.limits = limits
        self.gains = self._initialize_gains()
        
    async def calculate_control_inputs(
        self,
        state: Dict[str, np.ndarray],
        reference: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate stability control inputs"""
        # Calculate error signals
        errors = self._calculate_errors(state, reference)
        
        # Calculate damping terms
        damping = self._calculate_damping(state['angular_velocity'])
        
        # Calculate control surface deflections
        return {
            'elevator': self._calculate_elevator_command(errors, damping),
            'aileron': self._calculate_aileron_command(errors, damping),
            'rudder': self._calculate_rudder_command(errors, damping)
        }
        
    def _calculate_elevator_command(
        self,
        errors: Dict[str, float],
        damping: Dict[str, float]
    ) -> float:
        """Calculate elevator command for pitch stability"""
        # Pitch rate damping
        pitch_damping = -self.gains['q'] * damping['pitch']
        
        # Angle of attack limiting
        alpha_limit = np.clip(
            self.gains['alpha'] * (self.limits.max_angle_of_attack - errors['alpha']),
            -0.5, 0.5
        )
        
        return pitch_damping + alpha_limit
        
    def _calculate_aileron_command(
        self,
        errors: Dict[str, float],
        damping: Dict[str, float]
    ) -> float:
        """Calculate aileron command for roll stability"""
        # Roll rate damping
        roll_damping = -self.gains['p'] * damping['roll']
        
        # Bank angle control
        bank_control = self.gains['phi'] * errors['phi']
        
        return roll_damping + bank_control
        
    def _calculate_rudder_command(
        self,
        errors: Dict[str, float],
        damping: Dict[str, float]
    ) -> float:
        """Calculate rudder command for yaw stability"""
        # Yaw rate damping
        yaw_damping = -self.gains['r'] * damping['yaw']
        
        # Sideslip limiting
        beta_limit = np.clip(
            self.gains['beta'] * (self.limits.max_sideslip - errors['beta']),
            -0.3, 0.3
        )
        
        return yaw_damping + beta_limit


class AdaptiveStabilityController(StabilityAugmentationSystem):
    def __init__(self, limits: StabilityLimits):
        super().__init__(limits)
        self.velocity_ranges = {
            'subsonic': (0, 343),
            'transonic': (343, 686),
            'supersonic': (686, 1715),
            'hypersonic': (1715, np.inf)
        }
        
    async def calculate_control_inputs(
        self,
        state: Dict[str, np.ndarray],
        reference: Dict[str, float]
    ) -> Dict[str, float]:
        """Adapt control inputs based on velocity regime"""
        velocity = np.linalg.norm(state['velocity'])
        regime = self._identify_velocity_regime(velocity)
        
        # Adjust gains based on flight regime
        self._update_gains_for_regime(regime)
        
        # Calculate standard stability inputs
        return await super().calculate_control_inputs(state, reference)
        
    def _update_gains_for_regime(self, regime: str) -> None:
        """Adjust control gains for current velocity regime"""
        if regime == 'subsonic':
            self.gains = {'p': 0.8, 'q': 1.2, 'r': 0.6, 'phi': 0.5, 'alpha': 0.3, 'beta': 0.4}
        elif regime == 'transonic':
            self.gains = {'p': 1.0, 'q': 1.5, 'r': 0.8, 'phi': 0.7, 'alpha': 0.5, 'beta': 0.6}
        elif regime == 'supersonic':
            self.gains = {'p': 1.2, 'q': 1.8, 'r': 1.0, 'phi': 0.9, 'alpha': 0.7, 'beta': 0.8}
        else:  # hypersonic
            self.gains = {'p': 1.5, 'q': 2.0, 'r': 1.2, 'phi': 1.2, 'alpha': 1.0, 'beta': 1.0}