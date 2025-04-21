from typing import Dict, List, Any
import numpy as np
from ..navigation.path_planner import PathPlanner
from ..sensors.fusion.multi_sensor_fusion import MultiSensorFusion
from ..sensors.fusion.adaptive_prioritizer import AdaptivePrioritizer
from ..physics.models.unified_environment import UnifiedEnvironment
from .tactical_llm import TacticalLLM

class ContextAwarePlanner:
    def __init__(self):
        self.path_planner = PathPlanner({})
        self.fusion_module = MultiSensorFusion()
        self.adaptive_prioritizer = AdaptivePrioritizer()
        self.tactical_llm = TacticalLLM()
        self.environmental_context = None
        self.situational_context = None
        
    async def plan_context_aware_mission(
        self,
        mission_parameters: Dict[str, Any],
        sensor_data: Dict[str, Any],
        environment: UnifiedEnvironment
    ) -> Dict[str, Any]:
        # Update environmental context
        self.environmental_context = self._update_environmental_context(environment)
        
        # Fuse sensor data with adaptive prioritization
        fused_data = await self._fuse_sensor_data(sensor_data)
        
        # Update situational context
        self.situational_context = self._update_situational_context(
            fused_data,
            mission_parameters
        )
        
        # Generate context-aware path
        path_plan = await self._generate_context_aware_path(
            mission_parameters,
            fused_data
        )
        
        # Get tactical decision
        decision = await self.tactical_llm.generate_tactical_decision(
            sensor_data,
            mission_parameters
        )
        
        return {
            'path_plan': path_plan,
            'tactical_decision': decision,
            'context': {
                'environmental': self.environmental_context,
                'situational': self.situational_context
            }
        }
        
    def _update_environmental_context(
        self,
        environment: UnifiedEnvironment
    ) -> Dict[str, Any]:
        # Calculate environmental impact factors
        env_factors = self.adaptive_prioritizer._evaluate_environmental_impact(environment)
        
        return {
            'weather': environment.weather,
            'atmosphere': environment.atmosphere,
            'terrain': environment.terrain,
            'sensor_impacts': env_factors
        }
        
    async def _fuse_sensor_data(
        self,
        sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Calculate sensor priorities based on environmental context
        priorities = self.adaptive_prioritizer.calculate_sensor_priorities(
            self.environmental_context,
            {s: 1.0 for s in sensor_data.keys()}  # Assume perfect sensor health for now
        )
        
        # Fuse data with calculated priorities
        return await self.fusion_module.fuse_all_sensors(
            sensor_data['lidar'],
            sensor_data['magnetic'],
            sensor_data['spectral']
        )
        
    def _update_situational_context(
        self,
        fused_data: Dict[str, Any],
        mission_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            'target_state': fused_data['state'],
            'mission_objective': mission_parameters['objective'],
            'threat_level': self._assess_threat_level(fused_data, mission_parameters)
        }
        
    async def _generate_context_aware_path(
        self,
        mission_parameters: Dict[str, Any],
        fused_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Create context-aware cost factors
        cost_factors = self._create_context_aware_cost_factors(
            mission_parameters,
            fused_data
        )
        
        # Update path planner with context-aware costs
        self.path_planner.weight_factors = cost_factors
        
        return await self.path_planner.plan_path(
            fused_data['state']['position'],
            mission_parameters['goal_position'],
            self.environmental_context['terrain'],
            mission_parameters['obstacles']
        )
        
    def _create_context_aware_cost_factors(
        self,
        mission_parameters: Dict[str, Any],
        fused_data: Dict[str, Any]
    ) -> Dict[str, float]:
        base_factors = self.path_planner.weight_factors.copy()
        
        # Adjust factors based on situational context
        if fused_data['state']['classification']:
            # Increase obstacle avoidance weight when target detected
            base_factors['obstacles'] += 0.1
            
        if mission_parameters['stealth_required']:
            # Increase exposure cost when stealth is required
            base_factors['exposure'] += 0.1
            
        return base_factors
        
    def _assess_threat_level(
        self,
        fused_data: Dict[str, Any],
        mission_parameters: Dict[str, Any]
    ) -> float:
        # Simple threat assessment based on target detection and mission parameters
        if fused_data['state']['classification']:
            return 0.8  # High threat when target detected
        return 0.2  # Low threat when no target detected
    
    class ContextAwarePlanner:
        async def get_situational_context(self) -> Dict[str, Any]:
            """Get current situational context"""
            return {
                'threat_level': self.situational_context['threat_level'],
                'environment': self.environmental_context,
                'target_state': self.situational_context['target_state']
            }