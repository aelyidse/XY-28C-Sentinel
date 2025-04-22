from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from ..config.system_config import SystemConfig

class ComplianceLevel(Enum):
    FULL = 1
    PARTIAL = 2
    NON_COMPLIANT = 3

@dataclass
class ComplianceRule:
    rule_id: str
    description: str
    severity: int
    applicable_modes: List[str]

class ComplianceVerifier:
    def __init__(self, system_config: SystemConfig):
        self.config = system_config
        self.rules = self._load_compliance_rules()
        
    def verify_system_configuration(self) -> Dict[str, ComplianceLevel]:
        """Verify system configuration against compliance rules"""
        results = {}
        
        for rule in self.rules:
            if self.config.mode.value in rule.applicable_modes:
                compliance = self._check_config_rule(rule)
                results[rule.rule_id] = compliance
                
        return results
    
    def verify_mission_parameters(self, mission_params: Dict) -> Dict[str, ComplianceLevel]:
        """Verify mission parameters against compliance rules"""
        results = {}
        
        for rule in self.rules:
            if 'mission' in rule.applicable_modes:
                compliance = self._check_mission_rule(rule, mission_params)
                results[rule.rule_id] = compliance
                
        return results
    
    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load compliance rules from storage"""
        # Implementation would load from database or file
        return [
            ComplianceRule(
                rule_id="CONFIG-001",
                description="Minimum sensor update rate",
                severity=1,
                applicable_modes=["mission", "combat"]
            ),
            ComplianceRule(
                rule_id="MISSION-001",
                description="Maximum autonomous decision time",
                severity=2,
                applicable_modes=["mission", "combat"]
            )
        ]
    
    def _check_config_rule(self, rule: ComplianceRule) -> ComplianceLevel:
        """Check system configuration against a specific rule"""
        if rule.rule_id == "CONFIG-001":
            if self.config.sensor_update_rate >= 100.0:
                return ComplianceLevel.FULL
            elif self.config.sensor_update_rate >= 50.0:
                return ComplianceLevel.PARTIAL
            return ComplianceLevel.NON_COMPLIANT
        return ComplianceLevel.FULL
    
    def _check_mission_rule(self, rule: ComplianceRule, params: Dict) -> ComplianceLevel:
        """Check mission parameters against a specific rule"""
        if rule.rule_id == "MISSION-001":
            decision_time = params.get('max_decision_time', 0)
            if decision_time <= 0.5:
                return ComplianceLevel.FULL
            elif decision_time <= 1.0:
                return ComplianceLevel.PARTIAL
            return ComplianceLevel.NON_COMPLIANT
        return ComplianceLevel.FULL