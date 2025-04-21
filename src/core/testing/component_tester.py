from .test_generator import TestGenerator
from ..hil.hil_interface import HILInterface

class ComponentTester(TestGenerator):
    def __init__(self, event_manager, component_interfaces: Dict[str, HILInterface]):
        super().__init__(event_manager)
        self.components = component_interfaces
        
    async def generate_tests(self, component: str) -> List[Dict]:
        """Generate component-specific tests"""
        interface = self.components[component]
        capabilities = await interface.get_capabilities()
        
        tests = []
        for capability in capabilities:
            tests.extend(self._generate_capability_tests(capability))
            
        return tests
        
    def _generate_capability_tests(self, capability: Dict) -> List[Dict]:
        """Generate tests for specific capability"""
        tests = []
        
        # Boundary value tests
        if 'range' in capability:
            tests.append({
                'type': 'boundary_test',
                'parameters': {
                    'min': capability['range']['min'],
                    'max': capability['range']['max']
                }
            })
            
        # Stress tests
        if 'max_operating_conditions' in capability:
            tests.append({
                'type': 'stress_test',
                'parameters': capability['max_operating_conditions']
            })
            
        return tests