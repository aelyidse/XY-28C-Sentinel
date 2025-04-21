async def execute_mission_phase(
    self,
    phase: str,
    duration: float
) -> None:
    """Execute flight control for specific mission phase"""
    mission_phase = MissionPhase(phase)
    await self.mission_manager.set_mission_phase(mission_phase)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        throttle = await self.propulsion.get_throttle(elapsed)
        
        # Get flight controls based on phase
        controls = await self._calculate_phase_controls(mission_phase)
        
        # Apply controls with phase-specific throttle
        await self.apply_controls({
            **controls,
            'throttle': throttle
        })
        
        await asyncio.sleep(0.1)  # Control loop frequency


    async def _handle_propulsion_failure(self, failure_data: Dict[str, Any]) -> None:
        """Handle propulsion system failures"""
        failure_type = EmergencyMode[failure_data['failure_type'].upper()]
        await self.emergency_controller.activate_emergency_mode(failure_type)
        
        # Notify other systems
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.PROPULSION_EMERGENCY,
            component_id="propulsion_system",
            data={
                "failure_type": failure_type.name,
                "throttle_limit": self.propulsion.throttle,
                "timestamp": datetime.now()
            },
            priority=0
        ))

    # Add to existing class
    def __init__(self, propulsion_system, event_manager):
        super().__init__()
        self.emergency_controller = EmergencyPropulsionController(propulsion_system)
        self.event_manager = event_manager
        self.event_manager.subscribe(
            SystemEventType.PROPULSION_FAILURE.value, 
            self._handle_propulsion_failure
        )