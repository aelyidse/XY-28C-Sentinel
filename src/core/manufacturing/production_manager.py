from .production_simulator import ProductionSimulator
from .quality_predictor import QualityPredictor
from .scheduler import ProductionScheduler
from .supply_chain import SupplyChainModel

class ProductionManager:
    def __init__(self, event_manager):
        self.simulator = ProductionSimulator(event_manager)
        self.quality = QualityPredictor()
        self.scheduler = ProductionScheduler()
        self.supply_chain = SupplyChainModel()
        self.quality_control = QualityControlManager(event_manager)  # Add this line
        
    async def run_production_simulation(self, config: Dict) -> Dict[str, Any]:
        """Run complete production simulation"""
        # Simulate manufacturing processes
        process_results = await asyncio.gather(*[
            self.simulator.simulate_process(p['type'], p['params'])
            for p in config['processes']
        ])
        
        # Predict quality
        quality_results = [
            self.quality.predict_quality(p['type'], p['params'])
            for p in config['processes']
        ]
        
        # Optimize schedule
        schedule = self.scheduler.optimize_schedule(
            config['jobs'],
            config['resources']
        )
        
        # Optimize supply chain
        supply_chain = self.supply_chain.optimize_supply_chain(
            config['demand']
        )
        
        # Add quality validation
        quality_validation = await asyncio.gather(*[
            self.quality_control.validate_quality(p['type'], p['params'], pr)
            for p, pr in zip(config['processes'], process_results)
        ])
        
        return {
            'process_results': process_results,
            'quality_predictions': quality_results,
            'quality_validation': quality_validation,  # Add this line
            'schedule': schedule,
            'supply_chain': supply_chain
        }