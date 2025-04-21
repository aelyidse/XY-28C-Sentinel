import numpy as np
from typing import Dict

class MemoryOptimizer:
    def __init__(self, max_memory: float = 8.0):  # GB
        self.max_memory = max_memory * 1024**3  # Convert to bytes
        self.current_usage = 0
        
    def optimize_array(self, array: np.ndarray) -> np.ndarray:
        """Optimize array memory usage based on data type"""
        if array.dtype == np.float64:
            return array.astype(np.float32)
        elif array.dtype == np.int64:
            return array.astype(np.int32)
        return array
        
    def check_memory(self, data: Dict) -> bool:
        """Check if data can fit in available memory"""
        total = sum(
            arr.nbytes if isinstance(arr, np.ndarray) else 0 
            for arr in data.values()
        )
        return (self.current_usage + total) < self.max_memory
        
    def register_allocation(self, size: int) -> None:
        """Track memory allocations"""
        self.current_usage += size
        
    def release_memory(self, size: int) -> None:
        """Release allocated memory"""
        self.current_usage = max(0, self.current_usage - size)