import random
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ScenarioParameters:
    environment: str
    mission_type: str
    complexity_level: int
    target_count: int
    time_limit: int

class ScenarioGenerator:
    def __init__(self):
        self.environments = ['urban', 'rural', 'mountain', 'coastal']
        self.mission_types = ['surveillance', 'target_acquisition', 'electronic_warfare']
        
    def generate_scenario(self, complexity: int = 3) -> Dict:
        """Generate a random scenario based on complexity level"""
        params = ScenarioParameters(
            environment=random.choice(self.environments),
            mission_type=random.choice(self.mission_types),
            complexity_level=complexity,
            target_count=random.randint(1, complexity * 2),
            time_limit=random.randint(30, 120) * complexity
        )
        
        return self._build_scenario(params)
    
    def _build_scenario(self, params: ScenarioParameters) -> Dict:
        """Build scenario details based on parameters"""
        scenario = {
            'environment': params.environment,
            'mission_type': params.mission_type,
            'targets': self._generate_targets(params),
            'time_limit': params.time_limit,
            'constraints': self._generate_constraints(params)
        }
        return scenario
    
    def _generate_targets(self, params: ScenarioParameters) -> List[Dict]:
        """Generate target details"""
        targets = []
        for i in range(params.target_count):
            targets.append({
                'type': 'electronic' if params.mission_type == 'electronic_warfare' else 'physical',
                'location': self._generate_location(params.environment),
                'priority': random.randint(1, 3)
            })
        return targets
    
    def _generate_constraints(self, params: ScenarioParameters) -> Dict:
        """Generate scenario constraints"""
        return {
            'weather': random.choice(['clear', 'cloudy', 'rain', 'fog']),
            'visibility': random.randint(1, 10) * params.complexity_level,
            'electronic_interference': random.random() * params.complexity_level
        }
    
    def _generate_location(self, environment: str) -> Dict:
        """Generate location coordinates based on environment"""
        # Base coordinates for different environments
        base_coords = {
            'urban': (34.0522, -118.2437),  # Los Angeles
            'rural': (38.5072, -96.8005),    # Kansas
            'mountain': (39.1130, -106.4454), # Colorado
            'coastal': (36.7783, -119.4179)  # California
        }
        base = base_coords[environment]
        return {
            'latitude': base[0] + random.uniform(-0.5, 0.5),
            'longitude': base[1] + random.uniform(-0.5, 0.5)
        }