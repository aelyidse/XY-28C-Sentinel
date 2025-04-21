from typing import Dict
import asyncio
from ..events.event_manager import EventManager

class ManufacturingExecutionSystem:
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.active_processes = {}
        
    async def execute_manufacturing_plan(self, plan: Dict[str, Any]) -> None:
        """Execute manufacturing plan"""
        component = plan['component']
        self.active_processes[component] = {
            'status': 'running',
            'current_step': 0,
            'steps': plan['steps']
        }
        
        # Execute each step
        for i, step in enumerate(plan['steps']):
            await self._execute_manufacturing_step(component, i, step)
            
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.MANUFACTURING_COMPLETE,
            component_id=f"manufacturing_{component}",
            data={'status': 'complete'}
        ))
        
    async def _execute_manufacturing_step(self, component: str, step_num: int, step: Dict) -> None:
        """Execute individual manufacturing step"""
        # Update status
        self.active_processes[component]['current_step'] = step_num
        
        # Simulate step execution
        await asyncio.sleep(step['estimated_time'] * 3600)  # Convert hours to seconds
        
        # Publish progress update
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.MANUFACTURING_UPDATE,
            component_id=f"manufacturing_{component}",
            data={
                'step': step_num + 1,
                'total_steps': len(self.active_processes[component]['steps']),
                'process': step['process']
            }
        ))