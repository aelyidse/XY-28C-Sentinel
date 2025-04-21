class CounterJammingSystem:
    def __init__(self, secure_comms: SecureCommunication, em_sensor: EMSensor):
        self.secure_comms = secure_comms
        self.em_sensor = em_sensor
        self.jamming_threshold = 0.7  # Detection confidence threshold
        
    async def analyze_jamming(self, spectrum: np.ndarray) -> Dict:
        """Analyze spectrum for jamming patterns"""
        analysis = {
            'jamming_detected': False,
            'jamming_type': None,
            'confidence': 0.0,
            'affected_bands': []
        }
        
        # Calculate power statistics
        mean_power = np.mean(spectrum)
        std_power = np.std(spectrum)
        
        # Detect abnormal power levels
        if std_power > 15 or mean_power > self.em_sensor.jamming_effects['noise_floor'] + 20:
            analysis['jamming_detected'] = True
            analysis['confidence'] = min(1.0, (std_power / 20) * (mean_power / -50))
            
            if std_power > 20:
                analysis['jamming_type'] = 'NOISE'
            else:
                analysis['jamming_type'] = 'SPOT'
                
        return analysis
        
    async def activate_countermeasures(self, analysis: Dict) -> None:
        """Activate appropriate countermeasures based on jamming analysis"""
        if not analysis['jamming_detected']:
            return
            
        if analysis['jamming_type'] == 'NOISE':
            await self._handle_noise_jamming()
        elif analysis['jamming_type'] == 'SPOT':
            await self._handle_spot_jamming()
            
    async def _handle_noise_jamming(self) -> None:
        """Countermeasures for noise jamming"""
        # Reduce bandwidth and increase power
        await self.secure_comms.jamming_resistant.adapt_transmission()
        
    async def _handle_spot_jamming(self) -> None:
        """Countermeasures for spot jamming"""
        # Implement frequency hopping
        await self.secure_comms.start_frequency_hopping()