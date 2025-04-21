import numpy as np
from enum import Enum
from typing import Dict, List
from dataclasses import dataclass
from ..physics.models.electronic_vulnerability import ElectronicSystemType

class AttackPriority(Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1

@dataclass
class TargetVulnerability:
    system_type: ElectronicSystemType
    vulnerability_score: float
    strategic_value: float
    threat_level: float

class ElectronicAttackPrioritizer:
    def __init__(self):
        self.weights = {
            'vulnerability': 0.4,
            'strategic_value': 0.3,
            'threat_level': 0.3
        }
        
    def prioritize_targets(self, targets: List[TargetVulnerability]) -> List[Dict]:
        """Prioritize electronic attack targets based on multiple factors"""
        prioritized = []
        
        for target in targets:
            # Calculate composite score
            score = self._calculate_composite_score(target)
            
            # Determine priority level
            priority = self._determine_priority_level(score)
            
            prioritized.append({
                'target': target,
                'score': score,
                'priority': priority
            })
            
        # Sort by priority (highest first)
        prioritized.sort(key=lambda x: x['score'], reverse=True)
        return prioritized
        
    def _calculate_composite_score(self, target: TargetVulnerability) -> float:
        """Calculate weighted composite score"""
        return (
            self.weights['vulnerability'] * target.vulnerability_score +
            self.weights['strategic_value'] * target.strategic_value +
            self.weights['threat_level'] * target.threat_level
        )
        
    def _determine_priority_level(self, score: float) -> AttackPriority:
        """Convert score to priority level"""
        if score > 0.8:
            return AttackPriority.CRITICAL
        elif score > 0.6:
            return AttackPriority.HIGH
        elif score > 0.4:
            return AttackPriority.MEDIUM
        return AttackPriority.LOW