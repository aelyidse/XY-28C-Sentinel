from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import minimize

@dataclass
class CompositeLayer:
    material_type: str
    thickness: float  # mm
    orientation: float  # degrees
    properties: Dict[str, float]

@dataclass 
class CompositeMaterial:
    layers: List[CompositeLayer]
    stacking_sequence: List[int]
    symmetry: str = 'symmetric'

class CompositeOptimizer:
    def __init__(self):
        # Enhanced material mixing rules
        self.rule_of_mixtures = {
            'stiffness': lambda p1, p2, v: p1*v + p2*(1-v),
            'strength': lambda p1, p2, v: p1*v + p2*(1-v),
            'thermal_conductivity': lambda p1, p2, v: 1/(v/p1 + (1-v)/p2),
            'electrical_conductivity': lambda p1, p2, v: p1*v + p2*(1-v),
            'thermal_expansion': lambda p1, p2, v: (p1*v + p2*(1-v))/(1 + v*(p1/p2 - 1)),
            'dielectric_constant': lambda p1, p2, v: p1*v + p2*(1-v),
            'magnetic_permeability': lambda p1, p2, v: (p1*p2)/(p2*v + p1*(1-v))
        }
        
        # Environmental interaction coefficients
        self.environmental_factors = {
            'temperature_sensitivity': 0.02,  # Property change per degree C
            'humidity_sensitivity': 0.01,     # Property change per % RH
            'uv_degradation_rate': 0.005,    # Property degradation per hour of UV exposure
            'chemical_resistance': 0.95       # Retention factor for chemical exposure
        }

    def optimize_composite(
        self,
        target_properties: Dict[str, float],
        candidate_materials: List[Dict[str, Any]],
        constraints: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        """Optimize composite material composition and structure"""
        # Define optimization bounds
        bounds = [
            (0, 1) for _ in candidate_materials  # Volume fractions
        ] + [
            (0, 90) for _ in candidate_materials  # Fiber orientations
        ]

        # Initial guess (equal distribution)
        x0 = [1/len(candidate_materials)]*len(candidate_materials) + [0]*len(candidate_materials)

        # Run optimization
        res = minimize(
            fun=lambda x: self._composite_cost(x, target_properties, candidate_materials),
            x0=x0,
            bounds=bounds,
            constraints=self._build_constraints(constraints),
            method='SLSQP'
        )

        # Extract optimal parameters
        n = len(candidate_materials)
        volumes = res.x[:n]
        orientations = res.x[n:]

        # Add environmental considerations to optimization
        environment_adjusted_properties = self._adjust_for_environment(
            self._calculate_properties(volumes, orientations, candidate_materials),
            constraints.get('environment', {})
        )

        return {
            'composition': [
                {
                    'material': mat,
                    'volume_fraction': vol,
                    'orientation': ang,
                    'environmental_stability': self._calculate_environmental_stability(mat, constraints)
                }
                for mat, vol, ang in zip(candidate_materials, volumes, orientations)
            ],
            'achieved_properties': environment_adjusted_properties,
            'optimization_result': res,
            'environmental_performance': self._predict_environmental_performance(
                environment_adjusted_properties,
                constraints.get('environment', {})
            )
        }

    def _adjust_for_environment(
        self,
        properties: Dict[str, float],
        environment: Dict[str, float]
    ) -> Dict[str, float]:
        """Adjust material properties based on environmental conditions"""
        adjusted = properties.copy()
        
        # Temperature effects
        if 'temperature' in environment:
            delta_t = environment['temperature'] - 25  # Reference temperature
            for prop in adjusted:
                adjusted[prop] *= (1 + self.environmental_factors['temperature_sensitivity'] * delta_t)
        
        # Humidity effects
        if 'humidity' in environment:
            for prop in adjusted:
                adjusted[prop] *= (1 - self.environmental_factors['humidity_sensitivity'] * environment['humidity'])
        
        # UV exposure effects
        if 'uv_exposure' in environment:
            degradation = self.environmental_factors['uv_degradation_rate'] * environment['uv_exposure']
            for prop in adjusted:
                adjusted[prop] *= (1 - degradation)
        
        return adjusted

    def _calculate_environmental_stability(
        self,
        material: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> float:
        """Calculate material's stability under given environmental conditions"""
        stability_scores = []
        
        # Temperature stability
        if 'temperature_range' in constraints:
            min_temp, max_temp = constraints['temperature_range']
            temp_stability = self._evaluate_temperature_stability(material, min_temp, max_temp)
            stability_scores.append(temp_stability)
        
        # Chemical resistance
        if 'chemical_exposure' in constraints:
            chem_stability = material.get('properties', {}).get('chemical_resistance', 0.5)
            stability_scores.append(chem_stability * self.environmental_factors['chemical_resistance'])
        
        # UV resistance
        if 'uv_exposure' in constraints:
            uv_stability = 1 - (self.environmental_factors['uv_degradation_rate'] * 
                              constraints['uv_exposure'] * 
                              material.get('properties', {}).get('uv_sensitivity', 1.0))
            stability_scores.append(max(0, uv_stability))
        
        return np.mean(stability_scores) if stability_scores else 0.5

    def _predict_environmental_performance(
        self,
        properties: Dict[str, float],
        environment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict long-term performance under environmental conditions"""
        return {
            'thermal_cycling_stability': self._evaluate_thermal_cycling(properties, environment),
            'weathering_resistance': self._evaluate_weathering(properties, environment),
            'chemical_durability': self._evaluate_chemical_durability(properties, environment),
            'estimated_lifetime': self._estimate_lifetime(properties, environment)
        }

    def _composite_cost(
        self,
        x: np.ndarray,
        target: Dict[str, float],
        materials: List[Dict[str, Any]]
    ) -> float:
        """Calculate error between target and achieved properties"""
        n = len(materials)
        volumes = x[:n]
        orientations = x[n:]
        
        achieved = self._calculate_properties(volumes, orientations, materials)
        
        # Weighted sum of squared errors
        weights = {
            'stiffness': 1.0,
            'strength': 1.0,
            'density': 0.5,
            'thermal_conductivity': 0.8
        }
        
        return sum(
            weights.get(p, 1.0) * ((achieved[p] - target[p])/target[p])**2
            for p in target
        )

    def _calculate_properties(
        self,
        volumes: List[float],
        orientations: List[float],
        materials: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate effective composite properties"""
        # Normalize volumes
        total = sum(volumes)
        if total <= 0:
            return {k: 0 for k in materials[0]['properties']}
            
        volumes = [v/total for v in volumes]
        
        # Calculate effective properties
        properties = {}
        for prop in materials[0]['properties']:
            if prop in self.rule_of_mixtures:
                values = [m['properties'][prop] for m in materials]
                properties[prop] = self.rule_of_mixtures[prop](*values, *volumes)
            else:
                # Default to volume-weighted average
                properties[prop] = sum(
                    m['properties'][prop] * v 
                    for m, v in zip(materials, volumes)
                )
                
        return properties

    def _build_constraints(
        self,
        constraints: Dict[str, Tuple[float, float]]
    ) -> List[Dict[str, Any]]:
        """Build optimization constraints dictionary"""
        return [
            {'type': 'ineq', 'fun': lambda x: x[i] - lb}  # x[i] >= lb
            if ub is None else
            {'type': 'ineq', 'fun': lambda x: ub - x[i]}  # x[i] <= ub
            if lb is None else
            {'type': 'ineq', 'fun': lambda x: x[i] - lb}  # lb <= x[i] <= ub
            for i, (lb, ub) in enumerate(constraints.items())
        ]