from typing import Dict, List, Any
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from ..sensors.fusion.multi_sensor_fusion import MultiSensorFusion
from ..sensors.fusion.confidence_scorer import ConfidenceScorer

class TacticalLLM:
    def __init__(self, model_name: str = "tactical-decision"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.fusion_module = MultiSensorFusion()
        self.confidence_scorer = ConfidenceScorer()
        self.decision_thresholds = {
            'target_engagement': 0.85,
            'route_adjustment': 0.75,
            'sensor_reconfiguration': 0.65
        }
        
    async def generate_tactical_decision(
        self,
        sensor_data: Dict[str, Any],
        mission_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Fuse sensor data
        fused_data = await self.fusion_module.fuse_all_sensors(
            sensor_data['lidar'],
            sensor_data['magnetic'],
            sensor_data['spectral']
        )
        
        # Calculate confidence scores
        confidence_scores = self.confidence_scorer.compute_fusion_confidence(
            fused_data['confidence'],
            [],  # No temporal history for initial decision
            fused_data['features']
        )
        
        # Generate decision prompt
        prompt = self._create_decision_prompt(
            fused_data,
            confidence_scores,
            mission_parameters
        )
        
        # Get LLM response
        response = self._get_llm_response(prompt)
        
        # Parse and validate decision
        decision = self._parse_llm_response(response)
        validated_decision = self._validate_decision(decision, confidence_scores)
        
        return validated_decision
        
    def _create_decision_prompt(
        self,
        fused_data: Dict[str, Any],
        confidence_scores: Dict[str, float],
        mission_parameters: Dict[str, Any]
    ) -> str:
        prompt = f"""
        Mission Context:
        - Objective: {mission_parameters['objective']}
        - Current Location: {fused_data['state']['position']}
        - Confidence Scores: {confidence_scores}
        
        Sensor Data Summary:
        - Target Detection: {'Yes' if fused_data['state']['classification'] else 'No'}
        - Environmental Conditions: {mission_parameters['environment']}
        
        Required Decision:
        1. Target Engagement Assessment
        2. Route Optimization Recommendation
        3. Sensor Reconfiguration Needs
        
        Provide a JSON formatted response with the following structure:
        {{
            "target_engagement": <confidence_score>,
            "route_adjustment": <confidence_score>,
            "sensor_reconfiguration": <confidence_score>,
            "rationale": "<explanation>"
        }}
        """
        
        return prompt
        
    def _get_llm_response(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_length=512)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
        
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        try:
            # Extract JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            decision = json.loads(response[json_start:json_end])
            return decision
        except json.JSONDecodeError:
            # Handle parsing error
            return {
                'target_engagement': 0.0,
                'route_adjustment': 0.0,
                'sensor_reconfiguration': 0.0,
                'rationale': 'LLM response parsing failed'
            }
            
    def _validate_decision(
        self,
        decision: Dict[str, Any],
        confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        validated = {}
        
        for key, score in decision.items():
            if key in self.decision_thresholds:
                validated[key] = score if score >= self.decision_thresholds[key] else 0.0
            else:
                validated[key] = score
                
        # Add confidence-based validation
        avg_confidence = np.mean(list(confidence_scores.values()))
        if avg_confidence < 0.5:
            # Reduce all scores proportionally if confidence is low
            validated = {k: v * avg_confidence/0.5 for k, v in validated.items() if isinstance(v, (int, float))}
            
        return validated