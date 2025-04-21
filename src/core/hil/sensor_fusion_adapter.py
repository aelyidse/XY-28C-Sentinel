from ..sensors.fusion.multi_sensor_fusion import MultiSensorFusion
from typing import Dict, List

class SensorFusionHILAdapter:
    def __init__(self, fusion_module: MultiSensorFusion):
        self.fusion_module = fusion_module
        self.active_sensors = []

    async def add_sensor_stream(self, sensor_interface, sensor_type: str) -> None:
        """Add a sensor stream to the fusion pipeline"""
        def callback(data):
            return self._process_sensor_data(data, sensor_type)
            
        self.active_sensors.append({
            'interface': sensor_interface,
            'type': sensor_type,
            'task': asyncio.create_task(sensor_interface.stream_data(callback))
        })

    async def _process_sensor_data(self, data: Dict, sensor_type: str) -> None:
        """Process incoming sensor data for fusion"""
        if sensor_type == 'imu':
            await self.fusion_module.process_imu_data(data)
        elif sensor_type == 'gps':
            await self.fusion_module.process_gps_data(data)
        # Add other sensor types as needed