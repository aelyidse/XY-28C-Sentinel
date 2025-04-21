from typing import Dict
from .uav_airframe import UAVAirframeModel
from .propulsion_system import PropulsionSystemModel
from .camouflage_skin import CamouflageSkinModel

class CADManager:
    def __init__(self):
        self.models = {
            'airframe': UAVAirframeModel,
            'propulsion': PropulsionSystemModel,
            'camouflage': CamouflageSkinModel
        }
        self.active_models = {}
        
    def create_model(self, model_type: str, parameters: Dict[str, Any]) -> None:
        """Create new parametric model"""
        if model_type not in self.models:
            raise ValueError(f"Unknown model type: {model_type}")
            
        self.active_models[model_type] = self.models[model_type](parameters)
        
    def update_model(self, model_type: str, new_params: Dict[str, Any]) -> None:
        """Update existing model parameters"""
        if model_type not in self.active_models:
            raise ValueError(f"Model not created: {model_type}")
            
        self.active_models[model_type].update_parameters(new_params)
        
    def export_assembly(self, format: str = 'step') -> Dict[str, bytes]:
        """Export all models as assembly"""
        return {
            name: model.export_to_cad(format)
            for name, model in self.active_models.items()
        }