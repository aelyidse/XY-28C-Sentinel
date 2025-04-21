from typing import Dict
from ..hil.hil_interface import HILInterface
from .sensor_alignment import SensorAlignmentCalibrator

class CalibrationManager:
    def __init__(self, hil_interfaces: Dict[str, HILInterface], event_manager):
        self.hil_interfaces = hil_interfaces
        self.alignment_calibrator = SensorAlignmentCalibrator(event_manager)
        
    async def perform_system_calibration(self) -> Dict[str, Dict]:
        """Perform full system calibration"""
        results = {}
        
        # Perform sensor alignment
        alignment_results = await self.alignment_calibrator.perform_alignment(
            list(self.hil_interfaces.keys())
        )
        results['alignment'] = alignment_results
        
        # Perform individual sensor calibrations
        sensor_results = {}
        for name, interface in self.hil_interfaces.items():
            sensor_results[name] = await interface.calibrate()
            
        results['sensor'] = sensor_results
        
        return results