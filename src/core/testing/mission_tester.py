from .test_generator import TestGenerator
from ..digital_twin.scenarios import BASIC_SCENARIOS
from typing import Dict, List

class MissionTester(TestGenerator):
    def __init__(self, event_manager, digital_twin_manager):
        super().__init__(event_manager)
        self.digital_twin = digital_twin_manager
        
    async def generate_tests(self, mission_profile: str) -> List[Dict]:
        """Generate mission scenario tests"""
        scenarios = self._load_mission_scenarios(mission_profile)
        tests = []
        
        for scenario in scenarios:
            tests.append({
                'type': 'mission_scenario',
                'scenario': scenario,
                'validation_metrics': self._get_validation_metrics(scenario)
            })
            
        return tests
        
    def _load_mission_scenarios(self, profile: str) -> List[Dict]:
        """Load scenarios for specific mission profile"""
        return [
            s for s in BASIC_SCENARIOS 
            if s.get('mission_profile', 'default') == profile
        ]
        
    def _get_validation_metrics(self, scenario: Dict) -> Dict[str, float]:
        """Define validation metrics based on scenario type"""
        base_metrics = {
            'completion_rate': 0.95,
            'resource_efficiency': 0.85,
            'timing_accuracy': 0.90
        }
        
        if scenario.get('mission_profile') == 'recon':
            base_metrics.update({
                'stealth_maintenance': 0.95,
                'data_collection_quality': 0.90
            })
        elif scenario.get('mission_profile') == 'attack':
            base_metrics.update({
                'target_acquisition_accuracy': 0.95,
                'collateral_avoidance': 0.99
            })
        elif scenario.get('mission_profile') == 'evasion':
            base_metrics.update({
                'evasion_success_rate': 0.90,
                'energy_efficiency': 0.85
            })
            
        return base_metrics