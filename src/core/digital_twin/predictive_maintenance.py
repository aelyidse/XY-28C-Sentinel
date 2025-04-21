import numpy as np
from typing import Dict, List
from sklearn.ensemble import IsolationForest
from ..events.event_manager import EventManager

class PredictiveMaintenance:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.health_history = []
        self.models = {
            'propulsion': IsolationForest(contamination=0.05),
            'sensors': IsolationForest(contamination=0.03)
        }
        
    async def analyze_health_trends(self, component_data: Dict[str, List[float]]) -> Dict:
        """Analyze component health trends for predictive maintenance"""
        predictions = {}
        
        for component, data in component_data.items():
            # Reshape data for sklearn
            X = np.array(data).reshape(-1, 1)
            
            # Train model if not fitted
            if not hasattr(self.models[component], 'estimators_'):
                self.models[component].fit(X)
                
            # Predict anomalies
            anomalies = self.models[component].predict(X)
            predictions[component] = {
                'health_score': np.mean(data[-10:]),  # Moving average
                'anomaly_score': np.sum(anomalies == -1) / len(anomalies),
                'trend': self._calculate_trend(data)
            }
            
            # Publish event if anomaly detected
            if predictions[component]['anomaly_score'] > 0.1:
                await self.event_manager.publish(SystemEvent(
                    event_type=SystemEventType.MAINTENANCE_ALERT,
                    component_id=f"predictive_{component}",
                    data=predictions[component]
                ))
                
        return predictions
        
    def _calculate_trend(self, data: List[float]) -> float:
        """Calculate health trend using linear regression"""
        x = np.arange(len(data))
        slope = np.polyfit(x, data, 1)[0]
        return slope * 100  # Percentage change per time unit
        
    async def predict_failure_time(self, component: str, trend: float) -> float:
        """Predict time until failure based on health trend"""
        current_health = self.health_history[-1][component]
        return max(0, (current_health - 0.5) / -trend)  # Time until health reaches 0.5