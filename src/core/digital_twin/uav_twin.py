import numpy as np
from .digital_twin import DigitalTwin
from ..physics.models.aerodynamics import AerodynamicModel
from ..physics.models.propulsion import PropulsionModel

class UAVDigitalTwin(DigitalTwin):
    def __init__(self, physical_uav, event_manager, model_params: Dict):
        super().__init__(physical_uav, event_manager)
        self.aero_model = AerodynamicModel(model_params['aero'])
        self.prop_model = PropulsionModel(model_params['propulsion'])
        self.current_state = {}
        
    async def _update_digital_model(self, physical_state: Dict[str, Any]) -> None:
        """Update UAV digital model with physical state"""
        self.current_state = {
            'position': physical_state.get('position', np.zeros(3)),
            'velocity': physical_state.get('velocity', np.zeros(3)),
            'orientation': physical_state.get('orientation', np.array([1, 0, 0, 0])),
            'control_surfaces': physical_state.get('control_surfaces', {}),
            'propulsion': physical_state.get('propulsion', {}),
            'health': physical_state.get('health', 1.0)
        }
        
        # Update models if needed
        if 'aero_params' in physical_state:
            self.aero_model.update_parameters(physical_state['aero_params'])
            
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.DIGITAL_TWIN_UPDATED,
            component_id="uav_twin",
            data=self.current_state
        ))
        
    async def predict_state(self, delta_time: float) -> Dict[str, Any]:
        """Predict UAV state after delta_time"""
        # Calculate aerodynamic forces
        aero_forces = self.aero_model.calculate_forces(
            self.current_state['velocity'],
            self.current_state['orientation'],
            self.current_state['control_surfaces']
        )
        
        # Calculate propulsion forces
        prop_forces = self.prop_model.calculate_thrust(
            self.current_state['propulsion']
        )
        
        # Predict new state
        predicted = {
            'position': self.current_state['position'] + self.current_state['velocity'] * delta_time,
            'velocity': self.current_state['velocity'] + (aero_forces + prop_forces) * delta_time,
            'orientation': self._predict_orientation(delta_time),
            'control_surfaces': self.current_state['control_surfaces'],
            'propulsion': self.prop_model.predict_state(
                self.current_state['propulsion'],
                delta_time
            ),
            'health': max(0, self.current_state['health'] - 0.001 * delta_time)
        }
        
        return predicted