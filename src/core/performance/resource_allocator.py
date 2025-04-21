from typing import Dict, List
import psutil

class ResourceAllocator:
    def __init__(self):
        self.cpu_cores = psutil.cpu_count()
        self.gpu_count = self._detect_gpus()
        self.memory = psutil.virtual_memory().total
        
    def allocate_resources(self, tasks: List[Dict]) -> Dict:
        """Allocate resources based on task priorities and requirements"""
        allocations = {}
        available_cores = self.cpu_cores
        available_gpus = self.gpu_count
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda x: x['priority'], reverse=True)
        
        for task in sorted_tasks:
            req = task['requirements']
            alloc = {
                'cpu_cores': min(req.get('cpu_cores', 1), available_cores),
                'gpu': req.get('gpu', False) and available_gpus > 0,
                'memory': min(req.get('memory', 0), self.memory)
            }
            
            if alloc['cpu_cores'] > 0:
                allocations[task['id']] = alloc
                available_cores -= alloc['cpu_cores']
                if alloc['gpu']:
                    available_gpus -= 1
                    
        return allocations
        
    def _detect_gpus(self) -> int:
        """Detect available GPUs"""
        try:
            import cupy
            return cupy.cuda.runtime.getDeviceCount()
        except:
            return 0