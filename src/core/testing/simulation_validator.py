from .test_generator import TestGenerator
from scipy import stats

class SimulationValidator(TestGenerator):
    def __init__(self, event_manager, simulation_interface):
        super().__init__(event_manager)
        self.simulator = simulation_interface
        
    async def generate_tests(self, validation_type: str) -> List[Dict]:
        """Generate simulation validation tests"""
        tests = []
        
        if validation_type == 'statistical':
            tests.append({
                'type': 'ks_test',
                'parameters': {'samples': 1000}
            })
            
        elif validation_type == 'physical':
            tests.append({
                'type': 'physics_validation',
                'parameters': {'tolerance': 0.01}
            })
            
        return tests
        
    async def execute_test(self, test: Dict) -> Dict:
        """Execute simulation validation test"""
        if test['type'] == 'ks_test':
            return await self._run_ks_test(test)
        elif test['type'] == 'physics_validation':
            return await self._run_physics_validation(test)
            
    async def _run_ks_test(self, test: Dict) -> Dict:
        """Run Kolmogorov-Smirnov test for distribution validation"""
        samples = test['parameters']['samples']
        
        # Get simulated and real data
        simulated = self.simulator.generate_samples(samples)
        real = self._get_real_world_samples(samples)
        
        # Perform KS test
        ks_stat, p_value = stats.ks_2samp(simulated, real)
        
        return {
            'test_type': 'ks_test',
            'ks_statistic': ks_stat,
            'p_value': p_value,
            'pass': p_value > 0.05
        }