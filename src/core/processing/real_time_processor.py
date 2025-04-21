import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

class RealTimeProcessor:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._filters = []
        self._transforms = []

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with configured pipeline"""
        # Run intensive computations in thread pool
        processed = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._apply_pipeline,
            data
        )
        return processed

    def _apply_pipeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply processing pipeline to data"""
        for filter_fn in self._filters:
            data = filter_fn(data)
        
        for transform_fn in self._transforms:
            data = transform_fn(data)
            
        return data

    def add_filter(self, filter_fn):
        """Add data filter to pipeline"""
        self._filters.append(filter_fn)

    def add_transform(self, transform_fn):
        """Add data transform to pipeline"""
        self._transforms.append(transform_fn)