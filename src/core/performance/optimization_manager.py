from .distributed_manager import DistributedManager
from .gpu_accelerator import GPUAccelerator
from .memory_optimizer import MemoryOptimizer
from .resource_allocator import ResourceAllocator

class OptimizationManager:
    def __init__(self, event_manager):
        self.distributed = DistributedManager(event_manager)
        self.gpu = GPUAccelerator()
        self.memory = MemoryOptimizer()
        self.allocator = ResourceAllocator()
        
    async def optimize_simulation(self, sim_func, params: Dict) -> Dict:
        """Apply all optimization techniques to simulation"""
        # Check memory requirements
        if not self.memory.check_memory(params):
            raise MemoryError("Insufficient memory for simulation")
            
        # Get resource allocation
        allocation = self.allocator.allocate_resources([{
            'id': 'current_sim',
            'priority': params.get('priority', 1),
            'requirements': params.get('requirements', {})
        }])
        
        # Apply GPU acceleration if available
        if allocation.get('current_sim', {}).get('gpu', False):
            params = self._prepare_for_gpu(params)
            result = self.gpu.accelerate_physics(sim_func, params)
        else:
            # Distribute across CPU cores
            result = await self.distributed.distribute_simulation(
                sim_func,
                [params]
            )[0]
            
        return result
        
    def _prepare_for_gpu(self, params: Dict) -> Dict:
        """Prepare parameters for GPU processing"""
        return {
            k: self.memory.optimize_array(v) if isinstance(v, np.ndarray) else v
            for k, v in params.items()
        }