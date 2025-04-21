def calculate_power_requirements(
    self,
    target_color: np.ndarray,
    duration: float
) -> Dict[str, float]:
    """Calculate power requirements for color transition"""
    color_diff = np.linalg.norm(target_color - self.current_color)
    voltage = self._color_diff_to_voltage(
        color_diff,
        self.properties,
        self.current_temperature
    )
    
    return {
        'voltage': voltage,
        'current': voltage / self.properties.resistance,
        'power': voltage**2 / self.properties.resistance * duration,
        'energy': voltage**2 / self.properties.resistance * duration
    }

def optimize_for_power(
    self,
    target_color: np.ndarray,
    power_limit: float,
    duration: float
) -> Dict[str, Any]:
    """Optimize color transition within power limits"""
    requirements = self.calculate_power_requirements(target_color, duration)
    
    if requirements['power'] <= power_limit:
        return {
            'voltage': requirements['voltage'],
            'achievable_color': target_color,
            'power_used': requirements['power']
        }
        
    # Calculate maximum allowed voltage
    max_voltage = np.sqrt(power_limit * self.properties.resistance / duration)
    achievable_diff = (max_voltage - self.properties.voltage_range[0]) / \
                    (self.properties.voltage_range[1] - self.properties.voltage_range[0])
                    
    achievable_color = self.current_color + \
                      (target_color - self.current_color) * achievable_diff
                      
    return {
        'voltage': max_voltage,
        'achievable_color': achievable_color,
        'power_used': power_limit
    }