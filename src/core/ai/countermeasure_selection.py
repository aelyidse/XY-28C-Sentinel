from typing import Dict, Any
import numpy as np
from ..ew.attack_prioritizer import ElectronicAttackPrioritizer

class CountermeasureSelector:
    def __init__(self):
        self.attack_prioritizer = ElectronicAttackPrioritizer()
        
    def select_optimal_countermeasure(self, threat_analysis: Dict) -> Dict:
        """Select countermeasure with attack prioritization"""
        if 'electronic_vulnerability' in threat_analysis:
            targets = self._create_target_list(threat_analysis)
            prioritized = self.attack_prioritizer.prioritize_targets(targets)
            
            # Select highest priority target with effective countermeasure
            for target in prioritized:
                countermeasure = self._select_for_target(target['target'])
                if countermeasure:
                    return countermeasure
                    
        return self._select_default_countermeasure(threat_analysis)
        
    def _create_target_list(self, threat_analysis: Dict) -> List:
        """Create target list from threat analysis"""
        targets = []
        for sys_type, analysis in threat_analysis['electronic_vulnerability'].items():
            targets.append(TargetVulnerability(
                system_type=ElectronicSystemType(sys_type),
                vulnerability_score=1.0 - analysis['system_survival_probability'],
                strategic_value=self._get_strategic_value(sys_type),
                threat_level=threat_analysis['severity_score']
            ))
        return targets
    def _select_for_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Select and return the optimal countermeasure."""
        # Evaluate possible countermeasures
        countermeasures = [
            self._evaluate_stealth_mode(threat_analysis),
            self._evaluate_jamming_technique(threat_analysis),
            self._evaluate_evasive_action(threat_analysis)
        ]
        
        # Select best countermeasure based on effectiveness score
        best = max(countermeasures, key=lambda x: x['score'])
        return best['countermeasure']

    def _evaluate_stealth_mode(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate stealth mode countermeasure."""
        score = analysis['severity_score'] * 0.3
        params = {'mode': 'max_stealth'}
        return {'type': 'stealth', 'score': score, 'params': params}

    def _evaluate_jamming_technique(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate electronic jamming countermeasure."""
        score = analysis['severity_score'] * 0.4
        if analysis['threat_type'] == 'radar_lock':
            params = {'frequency': 2.5e9, 'strength': 80}
        else:
            params = {'frequency': 1.5e9, 'strength': 60}
        return {'type': 'jamming', 'score': score, 'params': params}

    def _evaluate_evasive_action(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate evasive action countermeasure."""
        score = analysis['severity_score'] * 0.3
        params = {'threat_position': analysis.get('predicted_position', np.array([0,0,0]))}
        return {'type': 'evasive_manoevers', 'score': score, 'params': params}