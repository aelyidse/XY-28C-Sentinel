import numpy as np
from scipy.optimize import minimize
from typing import Dict, List

class MorphingOptimizer:
    def __init__(self, morphing_model: MorphingSurface):
        self.model = morphing_model
        
    def optimize_control(
        self,
        target: Dict[str, float],
        flow_conditions: Dict[str, float],
        initial_guess: Dict[str, np.ndarray] = None
    ) -> Dict[str, Any]:
        """Optimize actuator voltages for target aerodynamic performance"""
        # Initialize optimization variables
        array_names = list(self.model.actuator_arrays.keys())
        n_actuators = {
            name: len(array.actuators)
            for name, array in self.model.actuator_arrays.items()
        }
        
        # Flatten initial guess
        if initial_guess is None:
            x0 = np.concatenate([
                np.zeros(n_actuators[name])
                for name in array_names
            ])
        else:
            x0 = np.concatenate([
                initial_guess[name]
                for name in array_names
            ])
            
        # Run optimization
        res = minimize(
            fun=lambda x: self._cost_function(x, target, flow_conditions, array_names, n_actuators),
            x0=x0,
            bounds=[(0, 1000)] * len(x0),  # 0-1000V typical range
            method='SLSQP'
        )
        
        # Reconstruct voltage arrays
        voltages = {}
        idx = 0
        for name in array_names:
            n = n_actuators[name]
            voltages[name] = res.x[idx:idx+n]
            idx += n
            
        return {
            'voltages': voltages,
            'performance': self._evaluate_performance(res.x, target, flow_conditions, array_names, n_actuators),
            'optimization_result': res
        }
        
    def _cost_function(
        self,
        x: np.ndarray,
        target: Dict[str, float],
        flow: Dict[str, float],
        array_names: List[str],
        n_actuators: Dict[str, int]
    ) -> float:
        """Calculate error between target and achieved performance"""
        performance = self._evaluate_performance(x, target, flow, array_names, n_actuators)
        
        weights = {
            'lift_coefficient': 1.0,
            'drag_coefficient': 0.8,
            'efficiency': 1.2
        }
        
        return sum(
            weights.get(k, 1.0) * ((performance[k] - target[k])/target[k])**2
            for k in target
        )
        
    def _evaluate_performance(
        self,
        x: np.ndarray,
        target: Dict[str, float],
        flow: Dict[str, float],
        array_names: List[str],
        n_actuators: Dict[str, int]
    ) -> Dict[str, float]:
        """Evaluate aerodynamic performance for given voltages"""
        # Reconstruct voltage arrays
        voltages = {}
        idx = 0
        for name in array_names:
            n = n_actuators[name]
            voltages[name] = x[idx:idx+n]
            idx += n
            
        # Calculate performance
        return self.model.calculate_aerodynamic_properties(
            control_voltages=voltages,
            flow_conditions=flow
        )