from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np

class ParametricModel(ABC):
    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters
        self._validate_parameters()
        
    @abstractmethod
    def _validate_parameters(self) -> None:
        """Validate input parameters"""
        pass
        
    @abstractmethod
    def generate_geometry(self) -> Dict[str, Any]:
        """Generate geometry from parameters"""
        pass
        
    @abstractmethod
    def export_to_cad(self, format: str = 'step') -> bytes:
        """Export model to CAD format"""
        pass
        
    def update_parameters(self, new_params: Dict[str, Any]) -> None:
        """Update model parameters"""
        self.parameters.update(new_params)
        self._validate_parameters()