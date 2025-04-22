from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

@dataclass
class CognitiveState:
    """Represents the current cognitive state of the system"""
    attention_focus: Dict[str, float]  # Priority weights for different aspects
    working_memory: Dict[str, Any]     # Current context and immediate data
    long_term_memory: List[Dict]       # Historical experiences and learned patterns
    emotional_state: Dict[str, float]  # System's internal state metrics

class CognitiveModule(ABC):
    """Base interface for cognitive modules"""
    
    @abstractmethod
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming data through the cognitive pipeline"""
        pass
    
    @abstractmethod
    async def update_state(self, state_delta: Dict[str, Any]) -> None:
        """Update the module's internal state"""
        pass
    
    @abstractmethod
    async def get_state(self) -> Dict[str, Any]:
        """Get current state of the cognitive module"""
        pass

class CognitiveArchitecture:
    """Main cognitive architecture implementation"""
    
    def __init__(self):
        self.state = CognitiveState(
            attention_focus={},
            working_memory={},
            long_term_memory=[],
            emotional_state={
                'arousal': 0.0,
                'valence': 0.0,
                'dominance': 0.0
            }
        )
        self.perception_module = PerceptionModule()
        self.reasoning_module = ReasoningModule()
        self.learning_module = LearningModule()
        self.action_module = ActionModule()
    
    async def process_sensory_input(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming sensory data through the cognitive pipeline"""
        # Perception stage
        perceived_data = await self.perception_module.process_input(sensor_data)
        
        # Update working memory with new perceptions
        self.state.working_memory.update(perceived_data)
        
        # Reasoning stage
        reasoning_result = await self.reasoning_module.process_input({
            'perceived_data': perceived_data,
            'working_memory': self.state.working_memory,
            'long_term_memory': self.state.long_term_memory
        })
        
        # Learning stage
        learning_update = await self.learning_module.process_input({
            'reasoning_result': reasoning_result,
            'current_state': self.state
        })
        
        # Update cognitive state
        await self._update_cognitive_state(learning_update)
        
        # Generate action plans
        action_plan = await self.action_module.process_input({
            'reasoning_result': reasoning_result,
            'cognitive_state': self.state
        })
        
        return action_plan
    
    async def _update_cognitive_state(self, update: Dict[str, Any]) -> None:
        """Update the cognitive state based on learning outcomes"""
        # Update attention focus
        if 'attention_update' in update:
            self.state.attention_focus.update(update['attention_update'])
        
        # Update emotional state
        if 'emotional_update' in update:
            self.state.emotional_state.update(update['emotional_update'])
        
        # Add to long-term memory if significant
        if 'memory_entry' in update:
            self.state.long_term_memory.append(update['memory_entry'])
            
        # Prune old memories if needed
        if len(self.state.long_term_memory) > 1000:  # Configurable limit
            self.state.long_term_memory = self.state.long_term_memory[-1000:]