from typing import Dict
from .component_tester import ComponentTester
from .mission_tester import MissionTester
from .adversarial_tester import AdversarialTester
from .simulation_validator import SimulationValidator

class TestManager:
    def __init__(self, system_components, ai_components, simulation_interface, digital_twin, event_manager):
        self.component_tester = ComponentTester(event_manager, system_components)
        self.mission_tester = MissionTester(event_manager, digital_twin)
        self.adversarial_tester = AdversarialTester(event_manager, ai_components)
        self.simulation_validator = SimulationValidator(event_manager, simulation_interface)
        
    async def run_comprehensive_test_suite(self) -> Dict:
        """Run all test types and return consolidated results"""
        results = {}
        
        # Component tests
        component_results = {}
        for component in self.component_tester.components:
            tests = await self.component_tester.generate_tests(component)
            component_results[component] = [
                await self.component_tester.execute_test(test)
                for test in tests
            ]
        results['components'] = component_results
        
        # Mission scenario tests
        mission_results = {}
        for profile in ['recon', 'attack', 'evasion']:
            tests = await self.mission_tester.generate_tests(profile)
            mission_results[profile] = [
                await self.mission_tester.execute_test(test)
                for test in tests
            ]
        results['missions'] = mission_results
        
        # AI adversarial tests
        ai_results = {}
        for ai_component in self.adversarial_tester.ai_components:
            tests = await self.adversarial_tester.generate_tests(ai_component)
            ai_results[ai_component] = [
                await self.adversarial_tester.execute_test(test)
                for test in tests
            ]
        results['ai_components'] = ai_results
        
        # Simulation validation
        sim_results = {}
        for val_type in ['statistical', 'physical']:
            tests = await self.simulation_validator.generate_tests(val_type)
            sim_results[val_type] = [
                await self.simulation_validator.execute_test(test)
                for test in tests
            ]
        results['simulation'] = sim_results
        
        return results