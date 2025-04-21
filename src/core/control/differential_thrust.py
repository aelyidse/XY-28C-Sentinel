import numpy as np
from typing import Dict

class DifferentialThrustController:
    def __init__(self, propulsion_system):
        self.propulsion = propulsion_system
        self.throttle_ratio = 0.5  # Default left/right split
        self.max_asymmetry = 0.3  # Maximum allowed thrust difference
        
    async def calculate_differential_thrust(
        self,
        yaw_rate_command: float,
        roll_rate_command: float
    ) -> Dict[str, float]:
        """Calculate asymmetric thrust for yaw/roll control"""
        # Calculate desired asymmetry
        yaw_asymmetry = np.clip(yaw_rate_command * 0.1, -self.max_asymmetry, self.max_asymmetry)
        roll_asymmetry = np.clip(roll_rate_command * 0.05, -self.max_asymmetry, self.max_asymmetry)
        
        # Combine effects
        total_asymmetry = yaw_asymmetry + roll_asymmetry
        left_throttle = 0.5 + total_asymmetry
        right_throttle = 0.5 - total_asymmetry
        
        return {
            'left': np.clip(left_throttle, 0, 1),
            'right': np.clip(right_throttle, 0, 1)
        }
        
    async def apply_differential_thrust(
        self,
        thrust_commands: Dict[str, float]
    ) -> None:
        """Apply differential thrust commands"""
        if not hasattr(self.propulsion, 'set_asymmetric_throttle'):
            raise RuntimeError("Differential thrust not supported")
            
        await self.propulsion.set_asymmetric_throttle(
            left=thrust_commands['left'],
            right=thrust_commands['right']
        )