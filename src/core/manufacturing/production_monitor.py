from typing import Dict, List
import time
from datetime import datetime
from .production_simulator import ProductionSimulator
from .supply_chain import SupplyChainModel

class ProductionMonitor:
    def __init__(self, simulator: ProductionSimulator, supply_chain: SupplyChainModel):
        self.simulator = simulator
        self.supply_chain = supply_chain
        self.metrics_history = []
        self.alerts = []
        
    async def monitor_production(self, config: Dict) -> Dict[str, Any]:
        """Monitor production processes in real-time"""
        start_time = time.time()
        
        # Track key metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'process_metrics': await self._get_process_metrics(config),
            'supply_chain_metrics': self._get_supply_chain_metrics(config),
            'quality_metrics': self._get_quality_metrics(config)
        }
        
        # Check for anomalies
        self._check_for_anomalies(metrics)
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        return {
            'metrics': metrics,
            'alerts': self.alerts,
            'monitoring_duration': time.time() - start_time
        }
        
    async def _get_process_metrics(self, config: Dict) -> Dict[str, Any]:
        """Get metrics from production processes"""
        metrics = {}
        for process in config['processes']:
            result = await self.simulator.simulate_process(process['type'], process['params'])
            metrics[process['type']] = {
                'completion_time': result.get('build_time', 0),
                'resource_utilization': result.get('resource_usage', {}),
                'throughput': result.get('throughput', 0)
            }
        return metrics
        
    def _get_supply_chain_metrics(self, config: Dict) -> Dict[str, Any]:
        """Get metrics from supply chain"""
        result = self.supply_chain.optimize_supply_chain(config['demand'])
        return {
            'delivery_times': result.get('delivery_times', {}),
            'inventory_levels': result.get('inventory', {}),
            'costs': result.get('total_cost', 0)
        }
        
    def _get_quality_metrics(self, config: Dict) -> Dict[str, Any]:
        """Get quality metrics"""
        # Placeholder for quality metrics
        return {
            'defect_rate': 0.0,
            'rework_rate': 0.0,
            'first_pass_yield': 1.0
        }
        
    def _check_for_anomalies(self, metrics: Dict) -> None:
        """Check for anomalies in production metrics"""
        # Check process metrics
        for process, data in metrics['process_metrics'].items():
            if data['completion_time'] > config['processes'][process]['max_time']:
                self.alerts.append({
                    'type': 'process_time_exceeded',
                    'process': process,
                    'value': data['completion_time']
                })
                
        # Check supply chain metrics
        if metrics['supply_chain_metrics']['costs'] > config['budget']:
            self.alerts.append({
                'type': 'budget_exceeded',
                'value': metrics['supply_chain_metrics']['costs']
            })
            
    def get_historical_metrics(self) -> List[Dict]:
        """Get historical monitoring data"""
        return self.metrics_history
        
    def clear_alerts(self) -> None:
        """Clear all active alerts"""
        self.alerts = []