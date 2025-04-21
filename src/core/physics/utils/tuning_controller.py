import numpy as np
from typing import Callable, Dict

class MetamaterialTuningController:
    def __init__(self, material):
        self.material = material
        self.voltage_history = []
        self.frequency_history = []
        
    def set_tuning_curve(self, response_fn: Callable) -> None:
        """Set custom voltage-to-frequency response"""
        self.material.tuning_response = response_fn
        
    def sweep_frequency(
        self,
        start: float,
        stop: float,
        steps: int,
        field_data: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Perform frequency sweep and record responses"""
        voltages = np.linspace(0, 10, steps)
        results = []
        
        for voltage in voltages:
            self.material.apply_tuning(voltage)
            response = MetamaterialEMPSimulation.calculate_tuned_response(
                self.material,
                field_data,
                self.material.resonant_frequency
            )
            results.append(response)
            self.voltage_history.append(voltage)
            self.frequency_history.append(self.material.resonant_frequency)
            
        return {
            'responses': results,
            'frequencies': self.frequency_history,
            'voltages': self.voltage_history
        }
        
    def find_optimal_tuning(
        self,
        target_frequency: float,
        field_data: np.ndarray,
        tolerance: float = 1e6  # 1 MHz
    ) -> Dict[str, Any]:
        """Find tuning voltage for exact frequency match"""
        def cost(voltage):
            self.material.apply_tuning(voltage)
            return abs(self.material.resonant_frequency - target_frequency)
            
        from scipy.optimize import minimize_scalar
        res = minimize_scalar(cost, bounds=(0, 10), method='bounded')
        
        if res.fun > tolerance:
            raise ValueError("Could not achieve target frequency within tolerance")
            
        return {
            'voltage': res.x,
            'achieved_frequency': self.material.resonant_frequency,
            'error': res.fun,
            'response': MetamaterialEMPSimulation.calculate_tuned_response(
                self.material,
                field_data,
                target_frequency
            )
        }