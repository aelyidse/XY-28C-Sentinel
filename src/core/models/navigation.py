from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class NavigationMode(Enum):
    AUTONOMOUS = "autonomous"
    MANUAL = "manual"
    EMERGENCY = "emergency"

@dataclass
class Position:
    latitude: float
    longitude: float
    altitude: float
    uncertainty: float  # meters

@dataclass
class Velocity:
    ground_speed: float  # m/s
    vertical_speed: float  # m/s
    heading: float  # degrees
    
@dataclass
class NavigationSystem:
    mode: NavigationMode
    current_position: Position
    current_velocity: Velocity
    target_position: Optional[Position]
    waypoints: List[Position]
    gps_satellites_tracked: int
    navigation_accuracy: float  # meters
    anti_jamming_active: bool