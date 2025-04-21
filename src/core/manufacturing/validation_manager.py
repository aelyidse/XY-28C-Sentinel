from .tolerance_analyzer import ToleranceAnalyzer
from .assembly_simulator import AssemblySimulator

class ManufacturingValidationManager:
    def __init__(self, event_manager):
        self.tolerance_analyzer = ToleranceAnalyzer()
        self.assembly_simulator = AssemblySimulator(event_manager)
        
    async def validate_component(self, component: str, dimensions: Dict[str, float]) -> Dict[str, Any]:
        """Run complete tolerance analysis for component"""
        analysis = self.tolerance_analyzer.analyze_component(component, dimensions)
        return analysis
        
    async def validate_assembly(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run complete assembly simulation and validation"""
        return await self.assembly_simulator.simulate_assembly(components)