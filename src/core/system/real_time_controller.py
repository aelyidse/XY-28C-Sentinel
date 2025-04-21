from typing import Dict, AsyncIterator
from ..hil.hil_interface import HILInterface

class RealTimeController:
    def __init__(self, hil_interfaces: Dict[str, HILInterface]):
        self.hil_interfaces = hil_interfaces
        self._tasks = []

    async def start_streaming(self, interface_name: str) -> AsyncIterator[Dict[str, Any]]:
        """Start streaming processed data from specified interface"""
        interface = self.hil_interfaces[interface_name]
        if not interface.connected:
            await interface.connect()
            
        if interface_name == 'imu':
            return interface.get_real_time_orientation()
        else:
            return interface.stream_processed_data(RealTimeProcessor())

    async def stop_all_streams(self) -> None:
        """Stop all active data streams"""
        for task in self._tasks:
            task.cancel()
        self._tasks = []