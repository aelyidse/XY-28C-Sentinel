from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator
import asyncio
from ..events.event_manager import EventManager

class HILInterface(ABC):
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.connected = False
        self.sampling_rate = 1000  # Hz
        self.calibration_data = {}
        self._processing_pipeline = None

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to physical hardware"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from hardware"""
        pass

    @abstractmethod
    async def read_sensor_data(self) -> Dict[str, Any]:
        """Read raw sensor data from hardware"""
        pass

    @abstractmethod
    async def collect_calibration_data(self) -> List[Dict]:
        """Collect data needed for calibration"""
        pass

    @abstractmethod
    async def apply_calibration(self, transform: np.ndarray) -> bool:
        """Apply calibration transformation to sensor"""
        pass

    @abstractmethod
    async def read_diagnostic_data(self) -> Dict[str, float]:
        """Read diagnostic data from hardware"""
        pass
    
    @abstractmethod
    async def perform_self_test(self) -> Dict[str, Any]:
        """Perform comprehensive self-test"""
        pass

    async def stream_data(self, callback) -> None:
        """Continuously stream sensor data"""
        while self.connected:
            data = await self.read_sensor_data()
            await callback(data)
            await asyncio.sleep(1/self.sampling_rate)

    async def stream_processed_data(self, processor) -> AsyncIterator[Dict[str, Any]]:
        """Stream processed sensor data in real-time"""
        async for raw_data in self._stream_raw_data():
            processed = await processor.process(raw_data)
            yield processed
            await asyncio.sleep(1/self.sampling_rate)

    async def _stream_raw_data(self) -> AsyncIterator[Dict[str, Any]]:
        """Internal raw data streaming"""
        while self.connected:
            yield await self.read_sensor_data()
            await asyncio.sleep(1/self.sampling_rate)

    def set_processing_pipeline(self, pipeline):
        """Set custom processing pipeline"""
        self._processing_pipeline = pipeline