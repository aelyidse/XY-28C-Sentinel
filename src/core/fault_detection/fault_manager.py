from typing import Dict
from ..hil.hil_interface import HILInterface
from .sensor_fault_detector import SensorFaultDetector

class FaultManager:
    def __init__(self, hil_interfaces: Dict[str, HILInterface], event_manager):
        self.detectors = {
            name: SensorFaultDetector(interface, event_manager)
            for name, interface in hil_interfaces.items()
        }
        self.active_faults = []
        
    async def monitor_components(self) -> None:
        """Continuously monitor all hardware components"""
        while True:
            for name, detector in self.detectors.items():
                data = await self.detectors[name].sensor.read_diagnostic_data()
                faults = await detector.detect_faults(data)
                
                for fault in faults:
                    diagnosis = await detector.diagnose_fault(fault)
                    self.active_faults.append({
                        'component': name,
                        'fault': fault,
                        'diagnosis': diagnosis,
                        'timestamp': datetime.now()
                    })
                    await detector.log_fault(fault)
                    
            await asyncio.sleep(1.0)  # Check every second
            
    async def get_component_health(self) -> Dict[str, float]:
        """Get health status for all components"""
        return {
            name: detector._calculate_health_score(
                await detector.sensor.read_diagnostic_data()
            )
            for name, detector in self.detectors.items()
        }