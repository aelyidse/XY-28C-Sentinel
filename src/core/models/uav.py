from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from .combat_element import CombatElement
from .sensors import SensorSystem
from .navigation import NavigationSystem
from .propulsion import PropulsionSystem
from ..config.system_config import SystemMode
from ..events.event_manager import EventManager
from .system_events import SystemEvent, SystemEventType

@dataclass
class StealthCharacteristics:
    radar_cross_section: float  # m²
    infrared_signature: float  # W/sr
    acoustic_signature: float  # dB
    visual_signature: float  # cd/m²

class UAVSystem:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self._setup_event_handlers()
        
        # Initialize threat analysis and countermeasure selector
        self.threat_analyzer = ThreatAnalyzer()
        self.countermeasure_selector = CountermeasureSelector()
        self.blockchain = CommandBlockchain()
        self.command_history = []
        self.secure_comms = SecureCommunication(self.blockchain)
        self.denied_ops = DeniedOperationsHandler(self)
        self.mesh_network = MeshNetwork(event_manager)
        self.autonomy_manager = AutonomyManager(self)
        self.em_sensor = EMSensor()
        self.jamming_simulator = JammingSimulator(self.em_sensor, event_manager)
        self.counter_jamming = CounterJammingSystem(self.secure_comms, self.em_sensor)
        self.deception_system = DeceptionSystem(self)
        self.secure_comm = SecureCommunicationManager(self.ionization_model)
        self.anti_hijack = AntiHijackManager(self.secure_comm)
        
    async def monitor_jamming(self) -> None:
        """Continuously monitor for jamming and activate countermeasures"""
        while True:
            spectrum = await self.em_sensor.get_em_spectrum()
            analysis = await self.counter_jamming.analyze_jamming(spectrum)
            
            if analysis['jamming_detected']:
                await self.counter_jamming.activate_countermeasures(analysis)
                
            await asyncio.sleep(0.1)
        
    async def start_secure_communication(self) -> None:
        """Start secure communication protocols"""
        await self.secure_comms.start_frequency_hopping()
        
    async def send_secure_message(self, message: str) -> bool:
        """Send message using secure protocol"""
        return await self.secure_comms.send_message(message)

    def _setup_event_handlers(self):
        self.event_manager.subscribe(SystemEventType.COMMUNICATION_SIGNAL_DETECTED.value, self._handle_communication_signal)
        self.event_manager.subscribe(SystemEventType.INTERFERENCE_DETECTED.value, self._handle_interference_detection)

    def _detect_interference(self, signal_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Locate the direction of interference sources using sensor fusion."""
        # Combine data from multiple sensors for better accuracy
        sensor_data = self._get_sensor_fusion_data()
        
        # Calculate time of arrival differences
        time_differences = self._calculate_time_of_arrival(sensor_data)
        
        # Determine direction of arrival
        direction = self._calculate_direction_of_arrival(time_differences)
        
        return direction if direction is not None else None

    def _calculate_direction_of_arrival(self, time_differences: np.ndarray) -> Optional[np.ndarray]:
        """Calculate the direction of interference based on time of arrival differences."""
        # Calculate angle using arctangent of time difference ratios
        if len(time_differences) < 2:
            return None
            
        # Convert time differences to distance differences
        distance_diff = time_differences * self.sensors.radar.sampling_frequency
        
        # Calculate direction in radians
        angle = np.arctan2(distance_diff[1], distance_diff[0])
        return np.array([angle, np.pi/2 - angle])  # Return both azimuth and elevation angles

    async def _handle_interference_detection(self, event: SystemEvent):
        """Process detected interference and calculate source location."""
        if not event.data:
            return
            
        # Calculate interference pattern
        interference_pattern = self._analyze_interference_pattern(event.data)
        
        if interference_pattern:
            # Calculate source location
            source_location = self._get_interference_source_location(
                interference_pattern['magnitude'],
                interference_pattern['phase']
            )
            
            # Publish detected source location
            await self.event_manager.publish(SystemEvent(
                event_type=SystemEventType.INTERFERENCE_LOCATED.value,
                component_id="uav_system",
                data={
                    "interference_source": source_location,
                    "detected_time": datetime.now()
                },
                timestamp=datetime.now(),
                priority=1,
                source_id=self.component_id
            ))

    def _analyze_interference_pattern(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interference pattern using multiple sensors."""
        # Get interference data from event
        return self.interference_calculator.compute_interference_pattern(
            signal_data['sources'],
            signal_data['observation_grid'],
            signal_data['time']
        )

    def _get_interference_source_location(self, magnitudes: np.ndarray, phases: np.ndarray) -> np.ndarray:
        """Calculate the most likely interference source location."""
        # Find the point of maximum constructive interference
        magnitude_peak = np.unravel_index(np.argmax(magnitudes), magnitudes.shape)
        
        # Calculate location based on peak phase characteristics
        return np.array([magnitude_peak[0], magnitude_peak[1], 
                        self._get_median_phase(phases[magnitude_peak])])

    def _get_median_phase(self, phase_values: np.ndarray) -> float:
        """Calculate the median phase angle for a given set of phase values."""
        return np.median(phase_values)

    async def _handle_communication_signal(self, event: SystemEvent):
        signal_data = event.data
        
        # Detect and handle jamming
        if await self.secure_comms.jamming_resistant.detect_jamming(signal_data):
            await self._activate_anti_jamming_protocol(signal_data)
            
        # Continue with normal communication handling
        if self._analyze_communication_signals(signal_data):
            await self._activate_anti_hijacking_protocol(signal_data)
            
    async def _activate_anti_jamming_protocol(self, signal_data: Dict[str, Any]):
        """Activate anti-jamming countermeasures"""
        # Adapt transmission parameters
        await self.secure_comms.jamming_resistant.adapt_transmission()
        
        # Notify systems
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.ANTI_JAMMING_ACTIVE,
            component_id="uav_system",
            data={"anti_jamming_mode": "active", "signal_response": signal_data},
            timestamp=datetime.now(),
            priority=1
        ))
        self.event_manager.subscribe(SystemEventType.THREAT_DETECTED.value, self._handle_threat)
        self.event_manager.subscribe(SystemEventType.TARGET_ACQUIRED.value, self._handle_target)
        self.event_manager.subscribe(SystemEventType.EMERGENCY_CONDITION.value, self._handle_emergency)
        self.event_manager.subscribe(SystemEventType.SYSTEM_FAILURE.value, self._handle_system_failure)

    async def _handle_threat(self, event: SystemEvent):
        """Process detected threats and select appropriate countermeasures."""
        threat_data = event.data
        
        # Analyze threat characteristics
        threat_analysis = await self.threat_analyzer.analyze_threat(threat_data)
        
        # Select optimal countermeasure
        selected_countermeasure = self.countermeasure_selector.select_optimal_countermeasure(
            threat_analysis
        )
        
        # Execute selected countermeasure
        await self._execute_countermeasure(selected_countermeasure)
        
        # Store threat analysis for ML training
        self._store_threat_analysis_for_ml(threat_analysis)
        
    async def _execute_countermeasure(self, countermeasure: Dict[str, Any]):
        """Execute the selected countermeasure."""
        if countermeasure['type'] == 'stealth':
            await self._activate_stealth_mode(countermeasure['params'])
        elif countermeasure['type'] == 'jamming':
            await self._deploy_electronic_jamming(countermeasure['params'])
        elif countermeasure['type'] == 'evasive_manoevers':
            await self._perform_evasive_action(countermeasure['params'])
        
    def _store_threat_analysis_for_ml(self, analysis: Dict[str, Any]):
        """Store threat analysis for machine learning training."""
        # Store analysis in memory and trigger periodic ML training
        self.threat_analysis_history.append(analysis)
        if len(self.threat_analysis_history) > 100:
            self._trainMachineLearningModel()
            
    async def _activate_stealth_mode(self, params: Dict[str, Any]):
        """Activate stealth mode with specified parameters."""
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.STEALTH_STATUS,
            component_id="uav_system",
            data={"stealth_mode": "active", "params": params},
            timestamp=datetime.now(),
            priority=1,
            source_id=self.component_id
        ))

    async def _deploy_electronic_jamming(self, params: Dict[str, Any]):
        """Deploy electronic jamming countermeasures."""
        # Implement jamming pattern generator
        jamming_pattern = self._generate_jamming_pattern(params['frequency'], params['strength'])
        
        # Publish jamming initiation event
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.ELECTRONIC_JAMMING_DEPLOYED,
            component_id="uav_system",
            data={"jamming_pattern": jamming_pattern, "params": params},
            timestamp=datetime.now(),
            priority=1,
            source_id=self.component_id
        ))

    async def _perform_evasive_action(self, params: Dict[str, Any]):
        """Perform evasive maneuvers to avoid threat."""
        # Calculate new trajectory
        new_position = self._calculate_evasive_trajectory(params['threat_position'])
        
        # Update navigation system
        await self.navigation.update_waypoint(new_position)
        
        # Publish evasion status
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.EVASIVE_MANOEUVRES_EXECUTED,
            component_id="uav_system",
            data={"new_position": new_position, "params": params},
            timestamp=datetime.now(),
            priority=1,
            source_id=self.component_id
        ))

    def _generate_jamming_pattern(self, frequency: float, strength: float) -> np.ndarray:
        """Generate a customized jamming pattern based on threat parameters."""
        # Create frequency modulation pattern
        modulation_index = strength / 100
        frequency_modulation = frequency * (1 + modulation_index * np.sin(np.linspace(0, 2*np.pi, 100)))
        
        return frequency_modulation

    def _calculate_evasive_trajectory(self, threat_position: np.ndarray) -> np.ndarray:
        """Calculate new trajectory to avoid threat."""
        current_position = self.navigation.current_position
        direction_vector = threat_position - current_position
        
        # Calculate perpendicular evasion vector
        evasion_vector = self._calculate_perpendicular_vector(direction_vector)
        
        # Calculate new position
        new_position = current_position + evasion_vector * 0.5
        
        return new_position

    def _calculate_perpendicular_vector(self, vector: np.ndarray) -> np.ndarray:
        """Calculate a perpendicular vector for evasion."""
        if vector.ndim != 1 or vector.size != 3:
            raise ValueError("Input vector must be 3-dimensional")
            
        # Rotate vector by 90 degrees around Z-axis
        perpendicular = np.array([
            -vector[1],
            vector[0],
            vector[2]
        ])
        
        return perpendicular / np.linalg.norm(perpendicular)

    async def _handle_target(self, event: SystemEvent):
        if self.system_mode == SystemMode.MISSION:
            await self._prepare_combat_element(event.data)
            
    async def _handle_emergency(self, event: SystemEvent):
        self.system_mode = SystemMode.EMERGENCY
        await self._initiate_emergency_protocol(event.data)
        
    async def _activate_countermeasures(self, threat_data: Dict[str, Any]):
        # Implement countermeasure logic
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.STEALTH_STATUS,
            component_id="uav_system",
            data={"stealth_mode": "active", "threat_response": threat_data},
            timestamp=datetime.now(),
            priority=1,
            source_id=self.component_id
        ))
        
    async def _prepare_combat_element(self, target_data: Dict[str, Any]):
        self.combat_element.deployment_ready = True
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.COMBAT_READY,
            component_id="uav_system",
            data={"target": target_data, "combat_ready": True},
            timestamp=datetime.now(),
            priority=1,
            source_id=self.component_id
        ))
        
    async def _initiate_emergency_protocol(self, emergency_data: Dict[str, Any]):
        failure_type = emergency_data.get('failure_type')
        if failure_type == 'critical':
            await self._execute_critical_failure_protocol(emergency_data)
        elif failure_type == 'navigation':
            await self._execute_navigation_failure_protocol(emergency_data)
        elif failure_type == 'communication':
            await self._execute_communication_failure_protocol(emergency_data)
        # Add more failure types as needed

    async def _execute_critical_failure_protocol(self, emergency_data: Dict[str, Any]):
        # Implement protocol for critical system failures
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.SYSTEM_STATUS_CHANGED,
            component_id="uav_system",
            data={"mode": "emergency", "status": "critical_failure"},
            timestamp=datetime.now(),
            priority=0,
            source_id=self.component_id
        ))

    async def _execute_navigation_failure_protocol(self, emergency_data: Dict[str, Any]):
        # Implement protocol for navigation system failures
        await self._switch_to_backup_navigation(emergency_data)

    async def _execute_communication_failure_protocol(self, emergency_data: Dict[str, Any]):
        # Implement protocol for communication system failures
        await self._activate_emergency_communication(emergency_data)
        
    async def update_system_status(self):
        status = self.get_mission_capability()
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.SYSTEM_STATUS_CHANGED,
            component_id="uav_system",
            data={
                "mission_capability": status,
                "power_remaining": self.power_remaining,
                "airframe_integrity": self.airframe_integrity
            },
            timestamp=datetime.now(),
            priority=2,
            source_id=self.component_id
        ))
    system_mode: SystemMode
    combat_element: CombatElement
    sensors: Dict[str, SensorSystem]
    navigation: NavigationSystem
    propulsion: PropulsionSystem
    stealth: StealthCharacteristics
    
    airframe_integrity: float  # percentage
    power_remaining: float  # percentage
    communication_status: bool
    anti_hijacking_active: bool
    
    def get_mission_capability(self) -> float:
        # Calculate overall mission capability based on subsystem states
        weights = {
            'combat': 0.4,
            'propulsion': 0.2,
            'navigation': 0.2,
            'sensors': 0.1,
            'power': 0.1
        }
        
        combat_ready = float(self.combat_element.deployment_ready)
        propulsion_ready = float(self.propulsion.fuel_remaining > 10.0)
        nav_ready = float(self.navigation.navigation_accuracy < 5.0)
        sensor_ready = float(all(s.calibration_matrix is not None for s in self.sensors.values()))
        power_ready = float(self.power_remaining > 20.0)
        
        return sum([
            weights['combat'] * combat_ready,
            weights['propulsion'] * propulsion_ready,
            weights['navigation'] * nav_ready,
            weights['sensors'] * sensor_ready,
            weights['power'] * power_ready
        ])

    def _analyze_communication_signals(self, signal_data: Dict[str, Any]) -> bool:
        # Analyze signal characteristics to detect anomalies
        frequency = signal_data.get('frequency')
        signal_strength = signal_data.get('signal_strength')
        # Check if signal characteristics match known hijacking patterns
        if self._is_hijacking_pattern(frequency, signal_strength):
            return True
        return False

    def _is_hijacking_pattern(self, frequency: float, signal_strength: float) -> bool:
        # Implement logic to identify hijacking patterns
        # For example, check if frequency is within a known control frequency range
        # and signal strength exceeds a certain threshold
        if (frequency > 2.4e9 and frequency < 2.5e9) and signal_strength > -50:
            return True
        return False

    async def _activate_anti_hijacking_protocol(self, signal_data: Dict[str, Any]):
        # Implement anti-hijacking logic
        # For example, change communication frequency or signal strength
        # or execute a counter-operator targeting protocol
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.ANTI_HIJACKING_ACTIVE,
            component_id="uav_system",
            data={"anti_hijacking_mode": "active", "signal_response": signal_data},
            timestamp=datetime.now(),
            priority=1,
            source_id=self.component_id
        ))
        self._initiate_signal_masking(signal_data)
        self._initiate_frequency_hopping()

    def _initiate_signal_masking(self, signal_data: Dict[str, Any]):
        # Analyze signal characteristics to determine masking parameters
        masking_parameters = self._determine_masking_parameters(signal_data)
        self._apply_signal_masking(masking_parameters)

    def _determine_masking_parameters(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement logic to determine masking parameters based on signal characteristics
        # For example, use signal strength and frequency to determine masking parameters
        masking_parameters = {'masking_frequency': 2.45e9, 'masking_strength': -30}
        return masking_parameters

    def _apply_signal_masking(self, masking_parameters: Dict[str, Any]):
        # Implement logic to apply signal masking
        # For example, use a signal generator to produce a masking signal
        masking_frequency = masking_parameters['masking_frequency']
        masking_strength = masking_parameters['masking_strength']
        
    def _get_sensor_fusion_data(self) -> Dict[str, np.ndarray]:
        """Get fused data from all active sensors."""
        fused_data = {
            'radar': self.sensors.radar.last_measurement,
            'rf': self.sensors.rf.last_measurement,
            'em': self.sensors.em.last_measurement
        }
        
        return self._fuse_sensor_data(fused_data)

    def _fuse_sensor_data(self, sensor_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Fuse data from multiple sensors using weighted average."""
        # Define confidence weights for each sensor type
        weights = {
            'radar': 0.5,
            'rf': 0.3,
            'em': 0.2
        }
        
        # Calculate confidence values
        confidences = {
            sensor: self._calculate_sensor_confidence(data)
            for sensor, data in sensor_data.items()
        }
        
        # Apply weights and calculate fused values
        fused_values = {
            sensor: data * (weights[sensor] * confidences[sensor])
            for sensor, data in sensor_data.items()
        }
        
        return {
            'magnitude': sum(fused_values.values()),
            'phase': np.mean([self._get_normalized_phase(data) for data in fused_values.values()], axis=0)
        }

    def _calculate_sensor_confidence(self, measurements: np.ndarray) -> float:
        """Calculate confidence in sensor measurements based on consistency."""
        if len(measurements) < 10:
            return 0.5
            
        # Calculate standard deviation of measurements
        std = np.std(measurements)
        
        # Return higher confidence for more consistent measurements
        return min(1.0, max(0.1, 1.0 - (std / np.mean(abs(measurements)))))

    def _get_normalized_phase(self, phase_values: np.ndarray) -> np.ndarray:
        """Normalize phase values to [-π, π] range."""
        return (phase_values + np.pi) % (2 * np.pi) - np.pi

    def predict_acoustic_signature(
        self,
        receiver_position: np.ndarray
    ) -> Dict[str, Any]:
        """Predict current acoustic signature at given position"""
        source_properties = AcousticProperties(
            frequency_range=(100, 5000),  # Hz
            directivity_pattern=self._get_directivity_pattern(),
            source_level=120,  # dB
            harmonic_content={
                1: 1.0,   # Fundamental
                2: 0.5,   # 1st harmonic
                3: 0.25   # 2nd harmonic
            }
        )
        
        return self.acoustic_predictor.predict_signature(
            source_properties=source_properties,
            position=self.navigation.current_position,
            receiver_position=receiver_position,
            velocity=self.navigation.current_velocity
        )
        
    def _get_directivity_pattern(self) -> np.ndarray:
        """Get current directivity pattern based on orientation"""
        # Simplified 360x180 degree pattern (azimuth x elevation)
        pattern = np.zeros((360, 180))
        
        # Create cardioid-like pattern forward direction
        for az in range(360):
            for el in range(180):
                # Convert to radians
                az_rad = np.radians(az)
                el_rad = np.radians(el)
                
                # Calculate directivity index (simplified)
                pattern[az, el] = 0.5 * (1 + np.cos(az_rad) * np.cos(el_rad))
                
        return pattern

    async def update_thermal_state(self) -> None:
        """Update thermal state based on current conditions"""
        flight_conditions = {
            'mach': self.navigation.current_mach,
            'altitude': self.navigation.current_altitude,
            'heat_flux': self._calculate_aero_heating()
        }
        await self.thermal_controller.update_thermal_state(flight_conditions)

    def _calculate_aero_heating(self) -> float:
        """Calculate aerodynamic heating rate"""
        # Using simplified convective heating equation
        rho = self.environment.atmosphere.density
        v = self.navigation.current_velocity
        return 0.5 * rho * (v**3) * 1e-6  # W/m²

async def _handle_thermal_event(self, event: SystemEvent) -> None:
    """Handle thermal-related system events"""
    if event.event_type == SystemEventType.THERMAL_OVERLOAD:
        await self.thermal_controller.set_mode(ThermalMode.EMERGENCY)
        await self._initiate_thermal_recovery_protocol(event.data)
        
    elif event.event_type == SystemEventType.STEALTH_MODE_ACTIVATED:
        await self.thermal_controller.set_mode(ThermalMode.STEALTH)
        
    elif event.event_type == SystemEventType.PERFORMANCE_MODE_ACTIVATED:
        await self.thermal_controller.set_mode(ThermalMode.PERFORMANCE)

async def _initiate_thermal_recovery_protocol(self, thermal_data: Dict[str, Any]) -> None:
    """Execute thermal recovery procedures"""
    # Reduce speed to lower heating
    await self.propulsion.set_throttle(0.5)
    
    # Maximize cooling
    await self.propulsion.cooling_system.set_max_cooling()
    
    # Notify systems
    await self.event_manager.publish(SystemEvent(
        event_type=SystemEventType.THERMAL_RECOVERY_ACTIVE,
        component_id="uav_system",
        data=thermal_data,
        timestamp=datetime.now(),
        priority=0
    ))

    async def execute_command(self, command: Dict[str, Any]) -> bool:
        """Execute command after security validation"""
        # Anti-hijacking check
        if not await self.anti_hijack.monitor_commands(command):
            await self.event_manager.publish(SystemEvent(
                event_type=SystemEventType.SECURITY_VIOLATION,
                component_id="uav_system",
                data={"command": command, "reason": "Anti-hijacking violation"},
                timestamp=datetime.now(),
                priority=0  # Highest priority
            ))
            return False
            
        # Proceed with existing blockchain validation
        # Create and validate transaction
        tx = self.blockchain.create_transaction(command)
        
        if not self.blockchain.validate_transaction(tx):
            await self.event_manager.publish(SystemEvent(
                event_type=SystemEventType.INVALID_COMMAND,
                component_id="uav_system",
                data={"command": command, "reason": "Blockchain validation failed"},
                timestamp=datetime.now(),
                priority=2
            ))
            return False
            
        # Add to chain and execute
        self.blockchain.add_block(tx)
        self.command_history.append(tx)
        
        # Execute command based on type
        if tx.command_type == "navigation":
            return await self._execute_navigation_command(tx.parameters)
        elif tx.command_type == "sensor":
            return await self._execute_sensor_command(tx.parameters)
        # ... other command types
        
        return True

    async def _validate_remote_command(self, command: Dict[str, Any]) -> bool:
        """Validate command from remote source using blockchain"""
        # This would interface with other nodes in the network
        proposed_chain = await self._get_proposed_chain_from_network()
        if not self.blockchain.consensus_validate(proposed_chain):
            return False
            
        # Check if command exists in validated chain
        command_hash = hashlib.sha256(json.dumps(command).encode()).hexdigest()
        return any(tx.command_id == command_hash for tx in proposed_chain)