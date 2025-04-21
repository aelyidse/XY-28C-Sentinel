from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt

class TradeoffAnalyzer:
    def analyze_tradeoffs(
        self,
        material_options: List[Dict[str, Any]],
        performance_targets: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze cost-performance tradeoffs for material options"""
        # Calculate Pareto front
        pareto_front = self._calculate_pareto_front(material_options, performance_targets)
        
        # Generate tradeoff curves
        tradeoff_curves = self._generate_tradeoff_curves(pareto_front)
        
        return {
            'pareto_front': pareto_front,
            'tradeoff_curves': tradeoff_curves,
            'optimal_selections': self._identify_optimal_points(pareto_front)
        }
        
    def _calculate_pareto_front(self, materials, targets) -> List[Dict[str, Any]]:
        """Calculate Pareto optimal material combinations"""
        pareto_points = []
        
        for mat in materials:
            # Calculate normalized performance metrics
            performance = sum(
                min(1, mat['properties'][p]/targets[p])
                for p in targets if p in mat['properties']
            ) / len(targets)
            
            pareto_points.append({
                'material': mat['name'],
                'performance': performance,
                'cost': mat['cost'],
                'environmental_impact': mat['environmental_impact']
            })
            
        # Sort and filter Pareto optimal points
        pareto_points.sort(key=lambda x: x['cost'])
        pareto_front = []
        max_perf = -np.inf
        
        for point in pareto_points:
            if point['performance'] > max_perf:
                pareto_front.append(point)
                max_perf = point['performance']
                
        return pareto_front