import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple
from scipy.integrate import solve_ivp

@dataclass
class VehicleState:
    position: np.ndarray  # [x, y, z] in meters (ECEF)
    velocity: np.ndarray  # [u, v, w] in m/s (body frame)
    orientation: np.ndarray  # [φ, θ, ψ] in radians (roll, pitch, yaw)
    angular_velocity: np.ndarray  # [p, q, r] in rad/s
    mass: float  # kg

class Hypersonic6DOF:
    def __init__(self, vehicle_params: Dict[str, Any]):
        self.params = vehicle_params
        self.g = 9.81
        self.inertia = self._calculate_inertia()
        self.stability_controller = StabilityAugmentationSystem(
            StabilityLimits(
                max_angle_of_attack=np.deg2rad(15),
                max_sideslip=np.deg2rad(5),
                max_roll_rate=np.deg2rad(100),
                max_pitch_rate=np.deg2rad(50),
                max_yaw_rate=np.deg2rad(30)
            )
        )
        self.envelope_protection = EnvelopeProtectionSystem(
            FlightEnvelope(
                max_mach=10.0,
                min_mach=0.3,
                max_altitude=50000,
                min_altitude=100,
                max_angle_of_attack=np.deg2rad(20),
                max_sideslip=np.deg2rad(10),
                max_g_load=9.0,
                max_roll_rate=np.deg2rad(120),
                max_pitch_rate=np.deg2rad(60),
                max_yaw_rate=np.deg2rad(40)
            )
        )
        self.propulsion_controller = IntegratedPropulsionController(
            vehicle_params['propulsion_system'],
            self
        )
        self.ionization_model = HypersonicIonizationModel(vehicle_params['environment'])
        self.ionization_state = {
            'electron_density': 0,
            'plasma_potential': 0,
            'critical_frequency': 0
        }

    async def _update_ionization_effects(self, velocity: float, altitude: float, surface_temp: float) -> None:
        """Update ionization state during flight"""
        material = IonizationProperties(
            work_function=4.5,  # Typical for aerospace alloys
            electron_density=self.ionization_state['electron_density'],
            recombination_rate=1e6,
            excitation_energy=15.6  # eV (for nitrogen)
        )
        
        results = await self.ionization_model.simulate_ionization(
            velocity=velocity,
            altitude=altitude,
            surface_temp=surface_temp,
            material=material,
            duration=0.1,  # Update every 100ms
            time_step=0.01
        )
        
        self.ionization_state = {
            'electron_density': results['electron_density'][-1],
            'plasma_potential': results['plasma_potential'][-1],
            'critical_frequency': results['critical_frequency'][-1]
        }

    async def simulate_trajectory(self, initial_state: VehicleState, controls: Dict[str, np.ndarray], duration: float, time_step: float = 0.01) -> Dict[str, np.ndarray]:
        """Simulate 6-DOF hypersonic flight"""
        # Flatten initial state for integration
        y0 = np.concatenate([
            initial_state.position,
            initial_state.velocity,
            initial_state.orientation,
            initial_state.angular_velocity,
            [initial_state.mass]
        ])
        
        # Solve equations of motion
        solution = solve_ivp(
            self._equations_of_motion,
            [0, duration],
            y0,
            t_eval=np.arange(0, duration, time_step),
            args=(controls,)
        )
        
        # Process results
        # Add ionization effects update
        for i, t in enumerate(solution.t):
            vel = np.linalg.norm(solution.y[3:6,i])
            alt = solution.y[2,i]
            temp = self._estimate_surface_temp(vel, alt)
            await self._update_ionization_effects(vel, alt, temp)
            
        return self._process_solution(solution)
        
    def _equations_of_motion(self, t: float, y: np.ndarray, controls: Dict[str, np.ndarray]) -> np.ndarray:
        """6-DOF equations of motion for hypersonic flight"""
        # Unpack state variables
        pos = y[:3]
        vel = y[3:6]
        angles = y[6:9]
        ang_vel = y[9:12]
        mass = y[12]
        
        # Get current controls
        throttle = controls['throttle'](t)
        elevon = controls['elevon'](t)
        rudder = controls['rudder'](t)
        
        # Calculate forces and moments
        forces = self._calculate_forces(vel, angles, throttle)
        moments = self._calculate_moments(vel, ang_vel, elevon, rudder)
        
        # Position derivatives (ECEF to body frame transform)
        pos_dot = self._euler_transform(angles).T @ vel
        
        # Velocity derivatives (F=ma)
        vel_dot = forces/mass - np.cross(ang_vel, vel)
        
        # Orientation derivatives
        angles_dot = self._euler_rates(angles, ang_vel)
        
        # Angular velocity derivatives (M=Iα)
        ang_vel_dot = np.linalg.inv(self.inertia) @ (moments - np.cross(ang_vel, self.inertia @ ang_vel))
        
        # Mass derivative (fuel consumption)
        mass_dot = -self._calculate_fuel_flow(throttle)
        
        return np.concatenate([pos_dot, vel_dot, angles_dot, ang_vel_dot, [mass_dot]])
        
    def _calculate_forces(
        self,
        velocity: np.ndarray,
        angles: np.ndarray,
        throttle: float
    ) -> np.ndarray:
        """Calculate total forces in body frame"""
        # Aerodynamic forces
        aero_forces = self._calculate_aerodynamic_forces(velocity, angles)
        
        # Propulsion forces
        # Get thrust vector (modified for thrust vectoring)
        if hasattr(self.params['propulsion_system'], 'vector_deflection'):
            pitch, yaw = self.params['propulsion_system'].vector_deflection
            thrust_dir = np.array([
                np.cos(pitch) * np.cos(yaw),
                np.sin(yaw),
                np.sin(pitch)
            ])
        else:
            thrust_dir = np.array([1, 0, 0])
            
        thrust = self.params['max_thrust'] * throttle * thrust_dir
        
        return aero_forces + thrust - gravity

    def _calculate_moments(
        self,
        velocity: np.ndarray,
        angular_velocity: np.ndarray,
        elevon: float,
        rudder: float
    ) -> np.ndarray:
        moments = np.zeros(3)
        
        # Aerodynamic moments (existing implementation)
        # ...
        
        # Add thrust vectoring moments if enabled
        if hasattr(self.params['propulsion_system'], 'vector_deflection'):
            pitch, yaw = self.params['propulsion_system'].vector_deflection
            thrust = self.params['max_thrust'] * throttle
            cog_to_nozzle = np.array([5.0, 0, 0])  # Distance from CG to nozzle [m]
            
            # Calculate moment arm from thrust vector deflection
            thrust_vector = thrust * np.array([
                np.cos(pitch) * np.cos(yaw),
                np.sin(yaw),
                np.sin(pitch)
            ])
            moments += np.cross(cog_to_nozzle, thrust_vector)
        
        return moments
        
    def _calculate_aerodynamic_forces(
        self,
        velocity: np.ndarray,
        angles: np.ndarray
    ) -> np.ndarray:
        """Calculate lift, drag, and side forces"""
        # Calculate dynamic pressure
        q = 0.5 * self.params['atmosphere'].density * np.linalg.norm(velocity)**2
        
        # Get aerodynamic coefficients (from aerodynamics simulation)
        alpha = np.arctan2(velocity[2], velocity[0])  # Angle of attack
        beta = np.arcsin(velocity[1]/np.linalg.norm(velocity))  # Sideslip angle
        
        # Transform coefficients to body axes
        ca, sa = np.cos(alpha), np.sin(alpha)
        cb, sb = np.cos(beta), np.sin(beta)
        
        # Force coefficients in body axes
        fx = -self.params['cd'](alpha) * ca * cb + self.params['cl'](alpha) * sa * cb
        fy = self.params['cy'](beta) * sb
        fz = -self.params['cd'](alpha) * sa + self.params['cl'](alpha) * ca
        
        return q * self.params['reference_area'] * np.array([fx, fy, fz])

    async def _calculate_stability_inputs(self, state: np.ndarray) -> Dict[str, float]:
        """Calculate stability augmentation inputs"""
        state_dict = {
            'position': state[:3],
            'velocity': state[3:6],
            'orientation': state[6:9],
            'angular_velocity': state[9:12]
        }
        
        reference = {
            'phi': 0,  # Target roll angle
            'theta': 0,  # Target pitch angle
            'alpha': 0,  # Target angle of attack
            'beta': 0  # Target sideslip
        }
        
        return await self.stability_controller.calculate_control_inputs(state_dict, reference)

    async def _check_envelope_protection(self, state: np.ndarray) -> Dict[str, float]:
        """Check and apply envelope protection"""
        state_dict = {
            'position': state[:3],
            'velocity': state[3:6],
            'orientation': state[6:9],
            'angular_velocity': state[9:12]
        }
        
        # Predict state 0.5 seconds ahead
        predicted_state = self._predict_state(state_dict, 0.5)
        
        violations = await self.envelope_protection.check_envelope_violations(
            state_dict,
            predicted_state
        )
        
        # Generate protection commands
        protection_commands = {}
        if violations['angle_of_attack'][0]:
            protection_commands['elevator'] = -0.5 * violations['angle_of_attack'][1]
        if violations['g_load'][0]:
            protection_commands['throttle'] = 0.8 - 0.3 * violations['g_load'][1]
            
        return protection_commands
        
        # Get integrated propulsion commands
        propulsion_commands = await self.propulsion_controller.calculate_propulsion_commands(
            flight_state=state_dict,
            control_inputs=controls
        )
        
        # Execute propulsion commands
        await self.propulsion_controller.execute_commands(propulsion_commands)