from typing import Dict, List
import numpy as np
from ..models.environment import UnifiedEnvironment
from ..models.electrochromic import ElectrochromicMaterial
from .camouflage_analysis import CamouflageAnalyzer

class AdaptiveCamouflageController:
    def __init__(self):
        self.analyzer = CamouflageAnalyzer()
        self.current_pattern = None
        self.environment_history = []
        self.electrochromic_materials = {}
        
    async def configure_materials(
        self,
        material_configs: Dict[str, Dict[str, Any]]
    ) -> None:
        """Configure electrochromic materials for camouflage"""
        from ..models.electrochromic import ElectrochromicProperties
        
        self.electrochromic_materials = {
            name: ElectrochromicMaterial(
                ElectrochromicProperties(
                    base_color=config['base_color'],
                    max_contrast=config['max_contrast'],
                    switching_time=config['switching_time'],
                    voltage_range=config['voltage_range'],
                    temperature_range=config['temperature_range'],
                    power_consumption=config['power_consumption']
                )
            )
            for name, config in material_configs.items()
        }
        
    async def _apply_color_pattern(
        self,
        pattern: Dict[str, Any],
        temperature: float
    ) -> Dict[str, Any]:
        """Apply color pattern using electrochromic materials"""
        results = {}
        for zone, material in self.electrochromic_materials.items():
            target_color = pattern['colors'][zone]
            voltage = pattern['voltages'][zone]
            
            results[zone] = material.calculate_color_response(
                target_color=target_color,
                voltage=voltage,
                temperature=temperature
            )
            
        return results
        
    async def update_camouflage(
        self,
        sensor_data: Dict[str, np.ndarray],
        environment: UnifiedEnvironment,
        flight_state: Dict[str, float]
    ) -> Dict[str, Any]:
        """Update camouflage based on current environment"""
        # Analyze environment
        analysis = await self.analyzer.analyze_environment(
            sensor_data,
            environment.atmosphere,
            environment.weather
        )
        
        # Generate optimal pattern
        optimal_pattern = analysis['recommended_pattern']
        
        # Adjust for flight dynamics
        adjusted_pattern = self._adjust_for_flight_dynamics(
            optimal_pattern,
            flight_state
        )
        
        # Update camouflage elements
        self.current_pattern = adjusted_pattern
        self.environment_history.append(analysis)
        
        return {
            'applied_pattern': adjusted_pattern,
            'analysis_results': analysis
        }
        
    def _adjust_for_flight_dynamics(
        self,
        pattern: Dict[str, Any],
        flight_state: Dict[str, float]
    ) -> Dict[str, Any]:
        """Adjust camouflage pattern for flight conditions"""
        # Adjust for velocity effects
        velocity_factor = np.clip(flight_state['velocity'] / 100, 0.1, 1.0)
        
        # Adjust pattern sharpness based on speed
        adjusted_pattern = {
            'color_pattern': {
                'colors': pattern['color_pattern']['colors'],
                'contrast': pattern['color_pattern']['contrast'] * velocity_factor
            },
            'thermal_pattern': {
                'gradient': pattern['thermal_pattern']['gradient'],
                'variation': pattern['thermal_pattern']['variation'] * velocity_factor
            },
            'texture_pattern': pattern['texture_pattern'],
            'update_rate': pattern['update_rate'] * (1 + flight_state['velocity'] / 50)
        }
        
        return adjusted_pattern
    
    async def optimize_pattern(
        self,
        environment: UnifiedEnvironment,
        flight_state: Dict[str, float],
        priority_zones: List[str] = None
    ) -> Dict[str, Any]:
        """Optimize camouflage pattern for current conditions"""
        if priority_zones is None:
            priority_zones = ['top', 'front', 'sides']
        
        # Get sensor data
        sensor_data = await self._collect_sensor_data()
        
        # Analyze environment
        analysis = await self.analyzer.analyze_environment(
            sensor_data,
            environment.atmosphere,
            environment.weather
        )
        
        # Optimize pattern weights based on priority zones
        optimized_pattern = self._optimize_zone_weights(
            analysis['recommended_pattern'],
            priority_zones,
            flight_state['velocity']
        )
        
        # Apply to materials
        applied_pattern = await self._apply_color_pattern(
            optimized_pattern,
            environment.atmosphere.temperature
        )
        
        return {
            'optimized_pattern': optimized_pattern,
            'applied_pattern': applied_pattern,
            'sensor_data': sensor_data
        }
    
    def _optimize_zone_weights(
        self,
        pattern: Dict[str, Any],
        priority_zones: List[str],
        velocity: float
    ) -> Dict[str, Any]:
        """Adjust pattern weights based on priority zones and velocity"""
        # Velocity-based scaling factor
        velocity_factor = np.clip(velocity / 200, 0.5, 1.5)
        
        # Adjust weights
        for zone in pattern['color_pattern']['zones']:
            if zone in priority_zones:
                pattern['color_pattern']['zones'][zone]['weight'] *= 1.5 * velocity_factor
            else:
                pattern['color_pattern']['zones'][zone]['weight'] *= 0.7 * velocity_factor
                
        return pattern
    
    async def optimize_power_consumption(
        self,
        pattern: Dict[str, Any],
        power_budget: float,
        mission_phase: str
    ) -> Dict[str, Any]:
        """Optimize camouflage pattern for power efficiency"""
        # Calculate current power requirements
        current_power = self._calculate_total_power(pattern)
        
        # Get priority zones based on mission phase
        priority_zones = self._get_priority_zones(mission_phase)
        
        # Optimize pattern within power budget
        optimized = self._optimize_pattern_power(
            pattern,
            current_power,
            power_budget,
            priority_zones
        )
        
        return {
            'optimized_pattern': optimized,
            'power_savings': current_power - self._calculate_total_power(optimized),
            'priority_zones': priority_zones
        }
    
    def _calculate_total_power(self, pattern: Dict[str, Any]) -> float:
        """Calculate total power consumption for pattern"""
        return sum(
            zone['power_consumption'] 
            for zone in pattern['color_pattern']['zones'].values()
        )
    
    def _get_priority_zones(self, mission_phase: str) -> List[str]:
        """Get priority zones based on mission phase"""
        phases = {
            'cruise': ['top', 'front'],
            'loiter': ['bottom', 'sides'],
            'attack': ['front', 'bottom'],
            'evade': ['all']
        }
        return phases.get(mission_phase, ['top', 'front'])
    
    def _optimize_pattern_power(
        self,
        pattern: Dict[str, Any],
        current_power: float,
        budget: float,
        priority_zones: List[str]
    ) -> Dict[str, Any]:
        """Optimize pattern to stay within power budget"""
        if current_power <= budget:
            return pattern
            
        # Calculate reduction factor
        reduction = budget / current_power
        
        # Apply reduction to non-priority zones first
        optimized = deepcopy(pattern)
        for zone in optimized['color_pattern']['zones']:
            if zone not in priority_zones:
                optimized['color_pattern']['zones'][zone]['contrast'] *= reduction * 0.7
                optimized['color_pattern']['zones'][zone]['update_rate'] *= reduction * 0.5
                
        # If still over budget, reduce priority zones
        if self._calculate_total_power(optimized) > budget:
            for zone in priority_zones:
                optimized['color_pattern']['zones'][zone]['contrast'] *= reduction * 0.9
                optimized['color_pattern']['zones'][zone]['update_rate'] *= reduction * 0.8
                
        return optimized