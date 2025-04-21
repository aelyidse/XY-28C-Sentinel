class MultiDomainSignatureAnalyzer:
    def __init__(self):
        # ... existing initialization ...
        self.acoustic_predictor = AcousticSignaturePredictor()
        
    def analyze_signature(
        self,
        sensor_data: Dict[str, Dict],
        known_signatures: List[Dict]
    ) -> Dict[str, Any]:
        # ... existing analysis ...
        
        # Add acoustic signature analysis
        if 'acoustic' in sensor_data:
            acoustic_results = self._analyze_acoustic_signature(
                sensor_data['acoustic'],
                known_signatures
            )
            results['acoustic'] = acoustic_results
            
        return results
        
    def _analyze_acoustic_signature(
        self,
        acoustic_data: Dict[str, Any],
        known_signatures: List[Dict]
    ) -> Dict[str, Any]:
        """Match observed acoustic signature against known patterns"""
        features = self._extract_acoustic_features(acoustic_data)
        matches = []
        
        for signature in known_signatures:
            if 'acoustic' not in signature:
                continue
                
            score = self._compare_acoustic_signatures(
                features,
                signature['acoustic']
            )
            
            if score >= self.min_confidence:
                matches.append({
                    'signature_id': signature['id'],
                    'confidence': score,
                    'type': 'acoustic'
                })
                
        return {
            'matches': matches,
            'features': features
        }
        
    def _extract_acoustic_features(
        self,
        acoustic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract key acoustic features for matching"""
        return {
            'spectral_peaks': self._find_spectral_peaks(acoustic_data['spectrum']),
            'harmonic_structure': self._analyze_harmonics(acoustic_data['spectrum']),
            'directivity': acoustic_data['directivity'],
            'temporal_features': self._analyze_temporal_features(acoustic_data['time_series'])
        }