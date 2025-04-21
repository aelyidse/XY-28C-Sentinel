from typing import Dict, Any
import numpy as np

class ScenarioTester:
    def __init__(self, digital_twin):
        self.twin = digital_twin
        self.scenario_results = []
        
    async def run_scenario(self, scenario: Dict[str, Any]) -> Dict:
        """Run what-if scenario on digital twin"""
        # Save original state
        original_state = self.twin.current_state
        
        # Apply scenario modifications
        modified_state = self._apply_scenario(original_state, scenario)
        
        # Run prediction
        result = await self.twin.predict_state(scenario['duration'])
        
        # Store and return results
        self.scenario_results.append({
            'scenario': scenario,
            'result': result,
            'timestamp': datetime.now()
        })
        
        # Restore original state
        await self.twin._update_digital_model(original_state)
        
        return result
        
    def _apply_scenario(self, state: Dict, scenario: Dict) -> Dict:
        """Apply scenario parameters to state"""
        modified = state.copy()
        
        if 'failure' in scenario:
            component = scenario['failure']['component']
            severity = scenario['failure']['severity']
            modified['health'] = max(0, modified['health'] - severity)
            
        if 'environment' in scenario:
            modified['environment'] = {
                **modified.get('environment', {}),
                **scenario['environment']
            }
            
        return modified
        
    async def compare_scenarios(self, scenarios: List[Dict]) -> Dict:
        """Compare multiple what-if scenarios"""
        results = {}
        
        for scenario in scenarios:
            results[scenario['name']] = await self.run_scenario(scenario)
            
        return results