from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np
from ..events.event_manager import EventManager

class TestGenerator(ABC):
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.test_history = []
        
    @abstractmethod
    async def generate_tests(self, component: str) -> List[Dict]:
        """Generate tests for specified component"""
        pass
        
    @abstractmethod
    async def execute_test(self, test: Dict) -> Dict:
        """Execute generated test"""
        pass
        
    async def log_test_result(self, result: Dict) -> None:
        """Log test execution results"""
        self.test_history.append(result)
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.TEST_EXECUTED,
            component_id="test_framework",
            data=result
        ))