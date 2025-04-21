from .test_generator import TestGenerator
import numpy as np

class AdversarialTester(TestGenerator):
    def __init__(self, event_manager, ai_components: Dict):
        super().__init__(event_manager)
        self.ai_components = ai_components
        
    async def generate_tests(self, component: str) -> List[Dict]:
        """Generate adversarial tests for AI components"""
        model = self.ai_components[component]
        tests = []
        
        # FGSM attack
        tests.append({
            'type': 'fgsm_attack',
            'parameters': {
                'epsilon': 0.1,
                'iterations': 10
            }
        })
        
        # Decision boundary exploration
        tests.append({
            'type': 'decision_boundary_test',
            'parameters': {
                'steps': 100,
                'dimensions': model.input_shape
            }
        })
        
        return tests
        
    async def execute_test(self, test: Dict) -> Dict:
        """Execute adversarial test"""
        if test['type'] == 'fgsm_attack':
            return await self._run_fgsm_attack(test)
        elif test['type'] == 'decision_boundary_test':
            return await self._run_decision_boundary_test(test)
            
    async def _run_fgsm_attack(self, test: Dict) -> Dict:
        """Run Fast Gradient Sign Method attack"""
        epsilon = test['parameters']['epsilon']
        iterations = test['parameters']['iterations']
        
        results = []
        for _ in range(iterations):
            # Generate adversarial example
            perturbation = epsilon * np.sign(np.random.randn(*model.input_shape))
            adversarial_input = np.clip(input_data + perturbation, 0, 1)
            
            # Get model predictions
            original_pred = model.predict(input_data)
            adversarial_pred = model.predict(adversarial_input)
            
            results.append({
                'input_diff': np.linalg.norm(perturbation),
                'output_diff': np.linalg.norm(original_pred - adversarial_pred)
            })
            
        return {'test_type': 'fgsm_attack', 'results': results}