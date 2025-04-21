from dataclasses import dataclass
from enum import Enum
from typing import Optional

class PropulsionMode(Enum):
    CRUISE = "cruise"
    SPRINT = "sprint"
    LOITER = "loiter"
    EMERGENCY = "emergency"

@dataclass
class ThermalState:
    surface_temperature: float  # K
    core_temperature: float  # K
    cooling_capacity: float  # W
    thermal_limit: float  # K

from ..physics.models.scramjet import ScramjetCFD, ScramjetGeometry
from ..physics.models.mhd_acceleration import MHDChannel, MHDAccelerator

@dataclass
class CoolingSystem:
    capacity: float  # W
    efficiency: float
    coolant_type: str
    active_zones: Dict[str, bool]
    
    async def calculate_cooling(
        self,
        heat_load: float,
        duration: float
    ) -> Dict[str, Any]:
        """Calculate cooling performance"""
        cooling_power = min(heat_load * self.efficiency, self.capacity)
        return {
            'heat_removed': cooling_power * duration,
            'residual_heat': max(0, heat_load - cooling_power),
            'efficiency': self.efficiency
        }

@dataclass
class ThrustVectoringConfig:
    max_deflection: float  # radians
    response_time: float  # seconds
    actuator_type: str  # 'electroactive' or 'hydraulic'

class PropulsionSystem(MultiStagePropulsion):
    def __init__(self):
        super().__init__()
        self.throttle_curve = {
            'initial': 0.5,
            'max': 0.8,
            'ramp_time': 5.0
        }
        self.left_throttle = 0.0
        self.right_throttle = 0.0
        self.thrust_vectoring = None
        self.cooling_system = None
        
    async def configure_cooling(
        self,
        capacity: float,
        efficiency: float,
        coolant_type: str = 'liquid_hydrogen'
    ) -> None:
        """Configure thermal management system"""
        self.cooling_system = CoolingSystem(
            capacity=capacity,
            efficiency=efficiency,
            coolant_type=coolant_type,
            active_zones={
                'nose': True,
                'leading_edges': True,
                'engine': True
            }
        )
        self.scramjet = None
        self.mhd_accelerator = None
        self.booster_model = None
        self.mode = PropulsionMode.CRUISE

    async def _calculate_booster_thrust(self, conditions: Dict[str, float]) -> Dict[str, Any]:
        """Calculate solid booster thrust"""
        if not self.booster_model:
            raise RuntimeError("Booster model not configured")
            
        return await self.booster_model.simulate_boost(
            burn_time=conditions['burn_time'],
            chamber_pressure=conditions['chamber_pressure']
        )

    async def _calculate_cruise_thrust(self, conditions: Dict[str, float]) -> Dict[str, Any]:
        """Calculate cruise thrust with residual MHD"""
        mhd_results = await self.calculate_mhd_thrust({
            'velocity': conditions['velocity'],
            'density': conditions['plasma_density'],
            'voltage': conditions.get('mhd_voltage', 1000)
        })
        return {
            'thrust': mhd_results['thrust'][-1] * 0.3,  # Reduced thrust
            'efficiency': mhd_results['efficiency'][-1],
            'stage': 'cruise'
        }

    def _combine_results(self, scram: Dict[str, Any], mhd: Dict[str, Any]) -> Dict[str, Any]:
        """Combine scramjet and MHD results"""
        return {
            'thrust': scram['thrust'] + mhd['thrust'],
            'efficiency': (scram['efficiency'] + mhd['efficiency']) / 2,
            'stage': 'mhd_acceleration',
            'scramjet': scram,
            'mhd': mhd
        }
        
    async def configure_scramjet(
        self,
        geometry: Dict[str, float],
        fuel_type: str = 'hydrogen'
    ) -> None:
        """Configure scramjet propulsion system"""
        scramjet_geom = ScramjetGeometry(
            inlet_area=geometry['inlet_area'],
            combustor_area=geometry['combustor_area'],
            nozzle_area=geometry['nozzle_area'],
            length=geometry['length']
        )
        self.scramjet = ScramjetCFD(scramjet_geom)
        self.fuel_type = fuel_type
        self.mode = PropulsionMode.SPRINT
        
    async def configure_mhd(
        self,
        channel_params: Dict[str, float],
        plasma_params: Dict[str, float]
    ) -> None:
        """Configure MHD acceleration system"""
        channel = MHDChannel(
            length=channel_params['length'],
            width=channel_params['width'],
            height=channel_params['height'],
            electrode_spacing=channel_params['electrode_spacing'],
            magnetic_field_strength=channel_params['magnetic_field']
        )
        self.mhd_accelerator = MHDAccelerator(channel, plasma_params)
        
    async def calculate_mhd_thrust(
        self,
        flow_conditions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate MHD acceleration performance"""
        if not self.mhd_accelerator:
            raise RuntimeError("MHD accelerator not configured")
            
        return await self.mhd_accelerator.simulate_acceleration(
            flow_velocity=flow_conditions['velocity'],
            plasma_density=flow_conditions['density'],
            applied_voltage=flow_conditions['voltage'],
            duration=1.0  # 1 second simulation
        )
    async def calculate_thrust(
        self,
        flight_conditions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate scramjet thrust for current flight conditions"""
        if not self.scramjet:
            raise RuntimeError("Scramjet not configured")
            
        conditions = ScramjetConditions(
            mach_number=flight_conditions['mach'],
            static_pressure=flight_conditions['pressure'],
            static_temperature=flight_conditions['temperature'],
            fuel_flow_rate=self._calculate_fuel_flow()
        )
        
        return await self.scramjet.simulate_flow(
            conditions,
            duration=1.0  # 1 second simulation
        )
    thrust_current: float  # N
    thrust_maximum: float  # N
    fuel_remaining: float  # kg
    mach_number: float
    thermal_state: ThermalState
    scramjet_active: bool = False
    mhd_acceleration: Optional[float] = None  # m/s²

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, List
import numpy as np

class PropulsionStage(Enum):
    SOLID_BOOSTER = auto()
    SCRAMJET = auto()
    MHD_ACCELERATION = auto()
    CRUISE = auto()

@dataclass
class StageTransition:
    velocity_threshold: float  # m/s
    altitude_threshold: float  # m
    temperature_limit: float  # K
    power_requirements: float  # W

class MultiStagePropulsion:
    def __init__(self):
        self.current_stage = PropulsionStage.SOLID_BOOSTER
        self.stage_transitions = {
            PropulsionStage.SOLID_BOOSTER: StageTransition(1500, 10000, 2000, 1e6),
            PropulsionStage.SCRAMJET: StageTransition(3000, 25000, 2500, 2e6),
            PropulsionStage.MHD_ACCELERATION: StageTransition(5000, 35000, 3000, 5e6)
        }
        self.stage_performance = {}

    async def configure_stages(
        self,
        scramjet_params: Dict[str, float],
        mhd_params: Dict[str, float]
    ) -> None:
        """Configure all propulsion stages"""
        await self.configure_scramjet(scramjet_params)
        await self.configure_mhd(mhd_params)
        self._initialize_performance_models()

    async def transition_stage(
        self,
        flight_conditions: Dict[str, float]
    ) -> PropulsionStage:
        """Determine and execute stage transition"""
        current_transition = self.stage_transitions[self.current_stage]
        
        if (flight_conditions['velocity'] >= current_transition.velocity_threshold and
            flight_conditions['altitude'] >= current_transition.altitude_threshold and
            flight_conditions['temperature'] <= current_transition.temperature_limit):
            
            if self.current_stage == PropulsionStage.SOLID_BOOSTER:
                self.current_stage = PropulsionStage.SCRAMJET
            elif self.current_stage == PropulsionStage.SCRAMJET:
                self.current_stage = PropulsionStage.MHD_ACCELERATION
            elif self.current_stage == PropulsionStage.MHD_ACCELERATION:
                self.current_stage = PropulsionStage.CRUISE
                
        return self.current_stage

    async def calculate_multi_stage_thrust(
        self,
        flight_conditions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate thrust for current stage"""
        stage = await self.transition_stage(flight_conditions)
        
        if stage == PropulsionStage.SOLID_BOOSTER:
            return await self._calculate_booster_thrust(flight_conditions)
        elif stage == PropulsionStage.SCRAMJET:
            return await self.calculate_thrust(flight_conditions)
        elif stage == PropulsionStage.MHD_ACCELERATION:
            scram_results = await self.calculate_thrust(flight_conditions)
            mhd_results = await self.calculate_mhd_thrust({
                'velocity': flight_conditions['velocity'],
                'density': flight_conditions['plasma_density'],
                'voltage': flight_conditions['mhd_voltage']
            })
            return self._combine_results(scram_results, mhd_results)
        else:  # CRUISE
            return await self._calculate_cruise_thrust(flight_conditions)

    async def configure_thrust_vectoring(
        self,
        config: ThrustVectoringConfig
    ) -> None:
        """Configure thrust vectoring system"""
        self.thrust_vectoring = config
        self.vector_deflection = np.zeros(2)  # [pitch, yaw] deflection in radians

    async def set_thrust_vector(
        self,
        pitch_deflection: float,
        yaw_deflection: float
    ) -> None:
        """Set thrust vector deflection angles"""
        if not self.thrust_vectoring:
            raise RuntimeError("Thrust vectoring not configured")
            
        # Apply deflection limits
        self.vector_deflection = np.array([
            np.clip(pitch_deflection, -self.thrust_vectoring.max_deflection, 
                   self.thrust_vectoring.max_deflection),
            np.clip(yaw_deflection, -self.thrust_vectoring.max_deflection,
                   self.thrust_vectoring.max_deflection)
        ])

    async def set_asymmetric_throttle(
        self,
        left: float,
        right: float
    ) -> None:
        """Set independent left/right throttle values"""
        self.left_throttle = np.clip(left, 0, 1)
        self.right_throttle = np.clip(right, 0, 1)
        
    async def get_total_thrust(self) -> float:
        """Get total thrust from both engines"""
        return (self.left_thrust() + self.right_thrust()) / 2
        
    def left_thrust(self) -> float:
        """Calculate left engine thrust"""
        return self._calculate_stage_thrust(self.left_throttle)
        
    def right_thrust(self) -> float:
        """Calculate right engine thrust"""
        return self._calculate_stage_thrust(self.right_throttle)

    async def set_throttle_curve(
        self,
        initial: float,
        max_throttle: float,
        ramp_time: float
    ) -> None:
        """Configure acceleration profile"""
        self.throttle_curve = {
            'initial': np.clip(initial, 0, 1),
            'max': np.clip(max_throttle, 0, 1),
            'ramp_time': max(0.1, ramp_time)
        }

    async def get_throttle(self, elapsed_time: float) -> float:
        """Get throttle setting based on acceleration profile"""
        if elapsed_time <= 0:
            return self.throttle_curve['initial']
            
        ramp_factor = min(1.0, elapsed_time / self.throttle_curve['ramp_time'])
        return self.throttle_curve['initial'] + \
               (self.throttle_curve['max'] - self.throttle_curve['initial']) * ramp_factor

    async def emergency_shutdown(self) -> None:
        """Execute controlled shutdown sequence"""
        await self.set_throttle(0)
        
        if hasattr(self, 'cooling_system'):
            await self.cooling_system.set_cooling_rate(1.0)  # Max cooling
            
        if hasattr(self, 'mhd_accelerator'):
            await self.configure_mhd_voltage(0)
            
        if hasattr(self, 'thrust_vectoring'):
            await self.set_thrust_vector(0, 0)

    async def _safety_checks(self) -> bool:
        """Perform critical system checks"""
        if self.thermal_state.core_temperature > self.thermal_state.thermal_limit:
            await self.event_manager.publish(SystemEvent(
                event_type=SystemEventType.PROPULSION_FAILURE,
                component_id="propulsion_system",
                data={"failure_type": "cooling_failure"},
                priority=0
            ))
            return False
        return True