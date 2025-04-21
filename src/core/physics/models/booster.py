import numpy as np
from dataclasses import dataclass

@dataclass
class SolidBooster:
    impulse: float  # N·s
    mass_flow_rate: float  # kg/s
    burn_rate_coefficient: float
    pressure_exponent: float

    async def simulate_boost(
        self,
        burn_time: float,
        chamber_pressure: float
    ) -> Dict[str, Any]:
        """Simulate solid booster performance"""
        time_points = np.linspace(0, burn_time, 100)
        thrust = []
        mass = []
        
        for t in time_points:
            # Calculate instantaneous thrust
            current_thrust = self.impulse * (1 - t/burn_time) * \
                           (chamber_pressure ** self.pressure_exponent) * \
                           self.burn_rate_coefficient
            thrust.append(current_thrust)
            mass.append(self.mass_flow_rate * t)
            
        return {
            'time': time_points,
            'thrust': np.array(thrust),
            'mass_consumed': np.array(mass),
            'total_impulse': np.trapz(thrust, time_points)
        }