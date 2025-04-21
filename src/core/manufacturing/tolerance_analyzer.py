import numpy as np
from typing import Dict, List
from scipy.stats import norm

class ToleranceAnalyzer:
    def __init__(self):
        self.tolerance_db = self._load_tolerance_standards()
        
    def analyze_component(self, component: str, dimensions: Dict[str, float]) -> Dict[str, Any]:
        """Perform tolerance analysis for component dimensions"""
        specs = self.tolerance_db.get(component, {})
        results = {}
        
        for dim, value in dimensions.items():
            if dim in specs:
                tol = specs[dim]
                results[dim] = self._calculate_tolerance_stats(value, tol)
                
        return {
            'component': component,
            'dimension_analysis': results,
            'stackup_analysis': self._calculate_stackup_tolerance(results)
        }
        
    def _calculate_tolerance_stats(self, nominal: float, tolerance: Dict) -> Dict[str, float]:
        """Calculate statistical tolerance metrics"""
        tol_type = tolerance['type']
        tol_value = tolerance['value']
        
        if tol_type == 'bilateral':
            min_val = nominal - tol_value
            max_val = nominal + tol_value
        elif tol_type == 'unilateral':
            min_val = nominal - tol_value if tolerance.get('direction') == 'minus' else nominal
            max_val = nominal if tolerance.get('direction') == 'minus' else nominal + tol_value
            
        return {
            'nominal': nominal,
            'min': min_val,
            'max': max_val,
            'cpk': self._calculate_cpk(nominal, min_val, max_val),
            'reject_rate': self._calculate_reject_rate(nominal, min_val, max_val)
        }
        
    def _calculate_stackup_tolerance(self, dim_results: Dict[str, Dict]) -> Dict[str, float]:
        """Calculate worst-case and statistical stackup"""
        variations = [d['max'] - d['min'] for d in dim_results.values()]
        return {
            'worst_case': sum(variations),
            'statistical': np.sqrt(sum(v**2 for v in variations))
        }