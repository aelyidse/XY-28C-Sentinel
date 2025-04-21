from typing import Dict, List
import numpy as np
from ..events.event_manager import EventManager

class AssemblySimulator:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.interference_threshold = 0.01  # mm
        
    async def simulate_assembly(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate assembly process with tolerance effects"""
        # Generate tolerance-affected geometries
        actual_geoms = self._apply_tolerances(components)
        
        # Check for interferences
        interferences = self._detect_interferences(actual_geoms)
        
        # Validate assembly
        validation = self._validate_assembly(actual_geoms)
        
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.ASSEMBLY_SIMULATION_COMPLETE,
            component_id="assembly_simulator",
            data={
                'interferences': interferences,
                'validation': validation
            }
        ))
        
        return {
            'components': actual_geoms,
            'interferences': interferences,
            'validation': validation
        }
        
    def _apply_tolerances(self, components: List[Dict]) -> List[Dict]:
        """Apply tolerance effects to nominal geometries"""
        return [
            {
                'name': c['name'],
                'geometry': self._perturb_geometry(c['geometry'], c['tolerances'])
            }
            for c in components
        ]
        
    def _detect_interferences(self, geometries: List[Dict]) -> List[Dict]:
        """Detect part interferences due to tolerance stacking"""
        interferences = []
        
        # Simple pairwise interference check
        for i, geom1 in enumerate(geometries):
            for j, geom2 in enumerate(geometries[i+1:], i+1):
                clearance = self._calculate_clearance(geom1, geom2)
                if clearance < -self.interference_threshold:
                    interferences.append({
                        'component_a': geom1['name'],
                        'component_b': geom2['name'],
                        'clearance': clearance
                    })
                    
        return interferences
        
    def _validate_assembly(self, geometries: List[Dict]) -> Dict[str, Any]:
        """Validate assembly meets functional requirements"""
        # Check critical dimensions
        critical_dims = self._check_critical_dimensions(geometries)
        
        # Check kinematic constraints
        kinematics = self._check_kinematic_constraints(geometries)
        
        return {
            'critical_dimensions': critical_dims,
            'kinematic_constraints': kinematics,
            'passed': all(critical_dims.values()) and all(kinematics.values())
        }