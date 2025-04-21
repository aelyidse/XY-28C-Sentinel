from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np
from scipy.integrate import odeint

@dataclass
class ElectrochromicProperties:
    base_color: Tuple[float, float, float]  # RGB (0-1)
    max_contrast: float  # 0-1
    switching_time: float  # seconds
    voltage_range: Tuple[float, float]  # min/max V
    temperature_range: Tuple[float, float]  # K
    power_consumption: float  # W/m²

class ElectrochromicMaterial:
    def __init__(self, properties: ElectrochromicProperties):
        self.properties = properties
        self.current_color = np.array(properties.base_color)
        self.current_voltage = 0.0
        
    def calculate_color_response(
        self,
        target_color: np.ndarray,
        voltage: float,
        temperature: float,
        duration: float = 1.0
    ) -> Dict[str, Any]:
        """Calculate color transition under applied voltage"""
        # Validate input voltage
        voltage = np.clip(voltage, *self.properties.voltage_range)
        
        # Calculate color change dynamics
        color_diff = target_color - self.current_color
        rate = self._calculate_switching_rate(voltage, temperature)
        
        # Solve color transition ODE
        t = np.linspace(0, duration, 10)
        colors = odeint(
            self._color_ode,
            self.current_color,
            t,
            args=(target_color, rate)
        )
        
        # Update state
        self.current_color = colors[-1]
        self.current_voltage = voltage
        
        return {
            'color_history': colors,
            'time_points': t,
            'power_consumption': self._calculate_power(voltage, duration),
            'achieved_color': colors[-1]
        }
        
    def _color_ode(
        self,
        color: np.ndarray,
        t: float,
        target: np.ndarray,
        rate: float
    ) -> np.ndarray:
        """ODE for color transition dynamics"""
        return rate * (target - color)
        
    def _calculate_switching_rate(
        self,
        voltage: float,
        temperature: float
    ) -> float:
        """Calculate voltage and temperature dependent switching rate"""
        # Normalized voltage effect (0-1)
        voltage_effect = (voltage - self.properties.voltage_range[0]) / \
                       (self.properties.voltage_range[1] - self.properties.voltage_range[0])
        
        # Temperature effect (0-1)
        temp_norm = np.clip(
            (temperature - self.properties.temperature_range[0]) / \
            (self.properties.temperature_range[1] - self.properties.temperature_range[0]),
            0, 1
        )
        
        # Combined rate
        return (voltage_effect * 0.7 + temp_norm * 0.3) / self.properties.switching_time
        
    def _calculate_power(
        self,
        voltage: float,
        duration: float
    ) -> float:
        """Calculate power consumption for transition"""
        return self.properties.power_consumption * \
               (voltage / self.properties.voltage_range[1]) * duration