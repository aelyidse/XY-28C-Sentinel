import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class PropulsionCommand:
    throttle: float  # 0-1
    scramjet_mode: str  # 'cruise', 'sprint', 'emergency'
    mhd_voltage: float  # V
    cooling_rate: float  # 0-1

class IntegratedPropulsionController:
    def __init__(self, propulsion_system, flight_dynamics):
        self.propulsion = propulsion_system
        self.flight = flight_dynamics
        self.last_command = PropulsionCommand(0, 'cruise', 0, 0)
        
    async def calculate_propulsion_commands(
        self,
        flight_state: Dict[str, Any],
        control_inputs: Dict[str, float]
    ) -> PropulsionCommand:
        """Calculate integrated propulsion commands"""
        # Get current flight conditions
        velocity = np.linalg.norm(flight_state['velocity'])
        altitude = flight_state['position'][2]
        
        # Calculate base throttle from control inputs
        throttle = self._calculate_base_throttle(control_inputs)
        
        # Adjust for flight envelope protection
        throttle = await self._adjust_for_envelope(flight_state, throttle)
        
        # Determine propulsion mode
        mode = self._determine_propulsion_mode(velocity, altitude)
        
        # Calculate MHD voltage based on velocity and altitude
        mhd_voltage = self._calculate_mhd_voltage(velocity, altitude)
        
        # Calculate cooling requirements
        cooling = await self._calculate_cooling_requirements(flight_state)
        
        return PropulsionCommand(
            throttle=throttle,
            scramjet_mode=mode,
            mhd_voltage=mhd_voltage,
            cooling_rate=cooling
        )
        
    async def execute_commands(self, command: PropulsionCommand) -> None:
        """Execute propulsion commands"""
        # Set propulsion mode
        if command.scramjet_mode == 'cruise':
            self.propulsion.mode = PropulsionMode.CRUISE
        elif command.scramjet_mode == 'sprint':
            self.propulsion.mode = PropulsionMode.SPRINT
        elif command.scramjet_mode == 'emergency':
            self.propulsion.mode = PropulsionMode.EMERGENCY
            
        # Apply throttle through propulsion system
        await self.propulsion.set_throttle(command.throttle)
        
        # Configure MHD system
        if self.propulsion.mhd_accelerator:
            await self.propulsion.configure_mhd_voltage(command.mhd_voltage)
            
        # Adjust cooling
        if self.propulsion.cooling_system:
            await self.propulsion.cooling_system.set_cooling_rate(command.cooling_rate)
            
        self.last_command = command
        
    def _calculate_base_throttle(self, control_inputs: Dict[str, float]) -> float:
        """Calculate base throttle setting from control inputs"""
        throttle = control_inputs.get('throttle', 0)
        
        # Apply nonlinear response curve for hypersonic regime
        if throttle > 0.7:
            return 0.7 + (throttle - 0.7) * 0.5
        return throttle
        
    async def _adjust_for_envelope(self, flight_state: Dict[str, Any], throttle: float) -> float:
        """Adjust throttle based on flight envelope limits"""
        violations = await self.flight.envelope_protection.check_envelope_violations(
            flight_state,
            None
        )
        
        # Reduce throttle if approaching mach limit
        if violations['mach'][0]:
            throttle *= (1 - violations['mach'][1] * 0.5)
            
        return np.clip(throttle, 0, 1)
        
    def _determine_propulsion_mode(self, velocity: float, altitude: float) -> str:
        """Determine optimal propulsion mode"""
        mach = velocity / 343.0
        
        if mach > 5.0 and altitude > 25000:
            return 'sprint'
        elif mach > 3.0:
            return 'cruise'
        return 'emergency'
        
    def _calculate_mhd_voltage(self, velocity: float, altitude: float) -> float:
        """Calculate MHD voltage based on flight conditions"""
        base_voltage = 1000  # V
        mach = velocity / 343.0
        
        # Voltage increases with mach and decreases with altitude
        voltage = base_voltage * (1 + mach/10) * (1 - altitude/100000)
        return np.clip(voltage, 0, 5000)
        
    async def _calculate_cooling_requirements(self, flight_state: Dict[str, Any]) -> float:
        """Calculate cooling system requirements"""
        if not hasattr(self.propulsion, 'cooling_system'):
            return 0
            
        velocity = np.linalg.norm(flight_state['velocity'])
        mach = velocity / 343.0
        
        # Cooling needs increase with mach^3
        cooling = min(1.0, (mach/5)**3)
        
        # Additional cooling if in high angle of attack
        alpha = np.arctan2(flight_state['velocity'][2], flight_state['velocity'][0])
        if abs(alpha) > np.deg2rad(10):
            cooling = min(1.0, cooling + 0.3)
            
        return cooling