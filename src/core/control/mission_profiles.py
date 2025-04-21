from enum import Enum
import numpy as np
from typing import Dict, List

class MissionPhase(Enum):
    STEALTH = "stealth"
    COMBAT = "combat"
    CRUISE = "cruise"
    EVASION = "evasion"
    ASCENT = "ascent"
    DESCENT = "descent"

class AccelerationProfile:
    def __init__(self, phase: MissionPhase):
        self.phase = phase
        self.throttle_curve = self._get_default_throttle_curve()
        self.mhd_settings = self._get_default_mhd_settings()
        
    def _get_default_throttle_curve(self) -> Dict[str, float]:
        """Get phase-specific throttle curve"""
        if self.phase == MissionPhase.STEALTH:
            return {'initial': 0.3, 'max': 0.5, 'ramp_time': 10.0}
        elif self.phase == MissionPhase.COMBAT:
            return {'initial': 0.8, 'max': 1.0, 'ramp_time': 2.0}
        elif self.phase == MissionPhase.EVASION:
            return {'initial': 0.9, 'max': 1.0, 'ramp_time': 1.0}
        else:  # CRUISE/ASCENT/DESCENT
            return {'initial': 0.5, 'max': 0.7, 'ramp_time': 5.0}
            
    def _get_default_mhd_settings(self) -> Dict[str, float]:
        """Get phase-specific MHD settings"""
        if self.phase in [MissionPhase.COMBAT, MissionPhase.EVASION]:
            return {'voltage': 5000, 'frequency': 100}
        elif self.phase == MissionPhase.STEALTH:
            return {'voltage': 2000, 'frequency': 50}
        else:
            return {'voltage': 3000, 'frequency': 75}

class MissionProfileManager:
    def __init__(self, propulsion_system):
        self.propulsion = propulsion_system
        self.current_phase = MissionPhase.CRUISE
        self.profiles = {
            phase: AccelerationProfile(phase) 
            for phase in MissionPhase
        }
        
    async def set_mission_phase(self, phase: MissionPhase) -> None:
        """Transition to new mission phase"""
        self.current_phase = phase
        profile = self.profiles[phase]
        
        # Configure propulsion for new phase
        await self._apply_acceleration_profile(profile)
        
    async def _apply_acceleration_profile(self, profile: AccelerationProfile) -> None:
        """Apply acceleration profile settings"""
        # Set throttle curve
        await self.propulsion.set_throttle_curve(
            initial=profile.throttle_curve['initial'],
            max_throttle=profile.throttle_curve['max'],
            ramp_time=profile.throttle_curve['ramp_time']
        )
        
        # Configure MHD system if available
        if hasattr(self.propulsion, 'configure_mhd'):
            await self.propulsion.configure_mhd(
                voltage=profile.mhd_settings['voltage'],
                frequency=profile.mhd_settings['frequency']
            )