class EMSensor:
    def __init__(self):
        self.frequency_range = (1e6, 18e9)  # 1MHz to 18GHz
        self.resolution = 1e6  # 1MHz resolution
        self.sensitivity = -90  # dBm
        self.jamming_effects = {
            'noise_floor': -100,
            'active_jammers': []
        }
        
    async def get_em_spectrum(self) -> np.ndarray:
        """Get current EM spectrum with jamming effects"""
        # Base spectrum with thermal noise
        spectrum = np.random.normal(
            loc=self.jamming_effects['noise_floor'],
            scale=10,
            size=int((self.frequency_range[1] - self.frequency_range[0]) / self.resolution)
        )
        
        # Add legitimate signals
        spectrum[1000:1100] += 30  # Simulated radar signal
        spectrum[5000:5100] += 20  # Simulated comms signal
        
        # Apply jamming effects
        for jammer in self.jamming_effects['active_jammers']:
            jam_start = int((jammer['frequency'] - jammer['bandwidth']/2 - self.frequency_range[0]) / self.resolution)
            jam_end = int((jammer['frequency'] + jammer['bandwidth']/2 - self.frequency_range[0]) / self.resolution)
            spectrum[jam_start:jam_end] += jammer['power']
            
        return spectrum
        
    def add_jammer(self, frequency: float, bandwidth: float, power: float) -> None:
        """Add a jamming signal to the simulation"""
        self.jamming_effects['active_jammers'].append({
            'frequency': frequency,
            'bandwidth': bandwidth,
            'power': power
        })
        
    def remove_jammer(self, frequency: float) -> None:
        """Remove a jamming signal from the simulation"""
        self.jamming_effects['active_jammers'] = [
            j for j in self.jamming_effects['active_jammers']
            if not (frequency - j['bandwidth']/2 <= j['frequency'] <= frequency + j['bandwidth']/2)
        ]