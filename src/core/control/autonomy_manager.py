from enum import Enum, auto
import numpy as np

class AutonomyLevel(Enum):
    DIRECTED = auto()       # Full human control (100% comms)
    ASSISTED = auto()      # Human-assisted (75-99% comms)
    SUPERVISED = auto()    # Human-supervised (50-74% comms)
    SEMI_AUTONOMOUS = auto() # Limited autonomy (25-49% comms)
    FULL_AUTONOMOUS = auto()  # Complete autonomy (0-24% comms)

class AutonomyManager:
    def __init__(self, uav_system):
        self.uav = uav_system
        self.current_level = AutonomyLevel.DIRECTED
        self.comm_quality_history = []
        
    def update_autonomy_level(self, comm_quality: float) -> None:
        """Update autonomy level based on communication quality (0-1 scale)"""
        previous_level = self.current_level
        
        if comm_quality > 0.75:
            self.current_level = AutonomyLevel.DIRECTED
        elif comm_quality > 0.5:
            self.current_level = AutonomyLevel.ASSISTED
        elif comm_quality > 0.25:
            self.current_level = AutonomyLevel.SUPERVISED
        elif comm_quality > 0.1:
            self.current_level = AutonomyLevel.SEMI_AUTONOMOUS
        else:
            self.current_level = AutonomyLevel.FULL_AUTONOMOUS
            
        if previous_level != self.current_level:
            self._notify_level_change()
            
    def _notify_level_change(self) -> None:
        """Notify systems about autonomy level change"""
        self.uav.event_manager.publish(SystemEvent(
            event_type=SystemEventType.AUTONOMY_LEVEL_CHANGED,
            component_id="autonomy_manager",
            data={
                "new_level": self.current_level.name,
                "timestamp": datetime.now()
            },
            priority=2
        ))
        
    def get_current_capabilities(self) -> Dict[str, Any]:
        """Get capabilities available at current autonomy level"""
        capabilities = {
            'navigation': self._get_navigation_capability(),
            'targeting': self._get_targeting_capability(),
            'countermeasures': self._get_countermeasure_capability()
        }
        return capabilities
        
    def _get_navigation_capability(self) -> Dict[str, bool]:
        """Get navigation capabilities based on autonomy level"""
        return {
            'waypoint_adjustment': self.current_level.value >= AutonomyLevel.SUPERVISED.value,
            'route_replanning': self.current_level.value >= AutonomyLevel.SEMI_AUTONOMOUS.value,
            'terrain_avoidance': True
        }
        
    def _get_targeting_capability(self) -> Dict[str, bool]:
        """Get targeting capabilities based on autonomy level"""
        return {
            'target_selection': self.current_level.value >= AutonomyLevel.ASSISTED.value,
            'weapon_release': self.current_level.value >= AutonomyLevel.SUPERVISED.value,
            'target_reacquisition': True
        }