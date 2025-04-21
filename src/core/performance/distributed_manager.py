import asyncio
from typing import Dict, List
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from ..events.event_manager import EventManager

class DistributedManager:
    def __init__(self, event_manager: EventManager, max_workers: int = 4):
        self.event_manager = event_manager
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.task_queue = asyncio.Queue()
        
    async def distribute_simulation(self, sim_func, params: List[Dict]) -> List[Dict]:
        """Distribute simulation tasks across processes"""
        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(self.executor, sim_func, param)
            for param in params
        ]
        return await asyncio.gather(*tasks)
        
    async def distribute_batch(self, tasks: List[Dict]) -> List[Dict]:
        """Distribute heterogeneous tasks with priority"""
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda x: x['priority'], reverse=True)
        
        results = []
        for task in sorted_tasks:
            result = await self.distribute_simulation(
                task['function'],
                task['parameters']
            )
            results.append(result)
            await self.event_manager.publish(SystemEvent(
                event_type=SystemEventType.DISTRIBUTED_TASK_COMPLETE,
                component_id="distributed_manager",
                data={
                    'task_id': task['id'],
                    'duration': task.get('duration', 0)
                }
            ))
            
        return results