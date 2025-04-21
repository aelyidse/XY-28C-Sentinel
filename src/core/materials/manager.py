from .database import MaterialDatabase
from .optimizer import MaterialOptimizer
from .durability import DurabilitySimulator
from .tradeoff import TradeoffAnalyzer

class MaterialManager:
    def __init__(self):
        self.database = MaterialDatabase()
        self.optimizer = MaterialOptimizer()
        self.durability = DurabilitySimulator()
        self.tradeoff = TradeoffAnalyzer()
        
    async def select_optimal_materials(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete material selection and optimization workflow"""
        # Query candidate materials
        candidates = self.database.query_materials(requirements['property_ranges'])
        
        # Run durability simulations
        durability_results = [
            self.durability.simulate_durability(
                m,
                requirements['environment'],
                requirements.get('mission_duration', 1000)
            )
            for m in candidates
        ]
        
        # Filter materials that meet durability requirements
        valid_materials = [
            m for m, dr in zip(candidates, durability_results)
            if dr['remaining_strength'] > requirements.get('min_strength', 0)
        ]
        
        # Optimize material selection
        optimization_result = self.optimizer.optimize_material_selection(
            requirements,
            valid_materials
        )
        
        # Analyze cost-performance tradeoffs
        tradeoff_analysis = self.tradeoff.analyze_tradeoffs(
            valid_materials,
            requirements['targets']
        )
        
        return {
            'optimization_result': optimization_result,
            'tradeoff_analysis': tradeoff_analysis,
            'durability_results': durability_results
        }