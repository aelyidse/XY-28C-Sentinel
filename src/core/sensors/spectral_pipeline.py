from typing import Dict, List, Tuple, Optional, AsyncIterator
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from asyncio import Queue
from .spectral_analyzer import SpectralAnalyzer
from .spectral_database import SpectralDatabase

class SpectralPipeline:
    def __init__(
        self,
        analyzer: SpectralAnalyzer,
        buffer_size: int = 10,
        max_workers: int = 4
    ):
        self.analyzer = analyzer
        self.data_queue = Queue(maxsize=buffer_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing = True
        
    async def process_stream(
        self,
        data_stream: AsyncIterator[Tuple[np.ndarray, Dict[str, Any]]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process real-time hyperspectral data stream"""
        try:
            async for frame_data, metadata in data_stream:
                # Queue frame for processing
                await self.data_queue.put((frame_data, metadata))
                
                # Process frame asynchronously
                result = await self._process_frame(frame_data, metadata)
                
                if result:
                    yield result
                    
        except Exception as e:
            self.processing = False
            raise e
            
    async def _process_frame(
        self,
        frame_data: np.ndarray,
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process individual hyperspectral frame"""
        try:
            # Run intensive computations in thread pool
            processed_data = await self._parallel_process(frame_data)
            
            # Analyze processed data
            analysis_result = await self.analyzer.analyze_hyperspectral_data(
                processed_data,
                metadata
            )
            
            return {
                'timestamp': metadata['timestamp'],
                'frame_id': metadata['frame_id'],
                'analysis': analysis_result,
                'processing_metadata': self._get_processing_metadata()
            }
            
        except Exception as e:
            print(f"Frame processing error: {e}")
            return None
            
    async def _parallel_process(
        self,
        frame_data: np.ndarray
    ) -> np.ndarray:
        """Execute parallel processing tasks"""
        # Split frame into chunks for parallel processing
        chunks = self._split_frame(frame_data)
        
        # Process chunks in parallel
        processed_chunks = await self._process_chunks(chunks)
        
        # Merge processed chunks
        return self._merge_chunks(processed_chunks)
        
    def _split_frame(
        self,
        frame: np.ndarray
    ) -> List[np.ndarray]:
        """Split frame into processable chunks"""
        return np.array_split(frame, self.executor._max_workers, axis=0)
        
    async def _process_chunks(
        self,
        chunks: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Process chunks in parallel using thread pool"""
        loop = asyncio.get_event_loop()
        tasks = []
        
        for chunk in chunks:
            task = loop.run_in_executor(
                self.executor,
                self._process_chunk,
                chunk
            )
            tasks.append(task)
            
        return await asyncio.gather(*tasks)
        
    def _process_chunk(
        self,
        chunk: np.ndarray
    ) -> np.ndarray:
        """Process individual chunk with optimized operations"""
        # Apply band-specific processing
        processed = self._apply_band_processing(chunk)
        
        # Apply noise reduction
        denoised = self._apply_noise_reduction(processed)
        
        # Apply feature enhancement
        enhanced = self._apply_feature_enhancement(denoised)
        
        return enhanced
        
    def _merge_chunks(
        self,
        chunks: List[np.ndarray]
    ) -> np.ndarray:
        """Merge processed chunks and handle boundaries"""
        return np.concatenate(chunks, axis=0)
        
    def _get_processing_metadata(self) -> Dict[str, Any]:
        """Get current processing pipeline metadata"""
        return {
            'queue_size': self.data_queue.qsize(),
            'processing_active': self.processing,
            'worker_count': self.executor._max_workers,
            'pipeline_latency': self._calculate_latency()
        }