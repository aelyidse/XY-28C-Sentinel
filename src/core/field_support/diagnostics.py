from typing import Dict, List
import numpy as np
from ..events.event_manager import EventManager

class FieldDiagnostics:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.diagnostic_rules = self._load_diagnostic_rules()
        
    async def run_diagnostics(self, system_state: Dict) -> Dict:
        """Run comprehensive system diagnostics"""
        # Check hardware status
        hardware_status = self._check_hardware(system_state)
        
        # Check software status
        software_status = self._check_software(system_state)
        
        # Check mission readiness
        mission_status = self._check_mission_readiness(system_state)
        
        # Generate troubleshooting steps
        troubleshooting = self._generate_troubleshooting(
            hardware_status,
            software_status,
            mission_status
        )
        
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.FIELD_DIAGNOSTICS_COMPLETE,
            component_id="field_support",
            data={
                'hardware': hardware_status,
                'software': software_status,
                'mission': mission_status
            }
        ))
        
        return {
            'status': {
                'hardware': hardware_status,
                'software': software_status,
                'mission': mission_status
            },
            'troubleshooting': troubleshooting
        }