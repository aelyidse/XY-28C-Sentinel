from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.signal import correlate2d
from sklearn.preprocessing import normalize
from .spectral_database import SpectralSignature, SpectralDatabase
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .environmental_compensation import EnvironmentalCompensator

class SpectralAnalyzer:
    def __init__(self, database: SpectralDatabase):
        self.database = database
        self.current_scan = None
        self.detection_threshold = 0.85
        self.feature_cache = {}
        self.max_cache_size = 100
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.compensator = EnvironmentalCompensator()
        self.feature_extractors = {
            'thermal': self._extract_thermal_features,
            'em': self._extract_em_features,
            'rf': self._extract_rf_features,
            'spatial': self._extract_spatial_features
        }
        self.wavelength_bands = {
            'visible': (380, 750),  # nm
            'nir': (750, 1400),     # nm
            'swir': (1400, 3000),   # nm
            'thermal': (3000, 14000) # nm
        }
        
    async def analyze_hyperspectral_data(
        self,
        spectral_data: np.ndarray,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Use cached features if available
        cache_key = self._generate_cache_key(spectral_data)
        if cache_key in self.feature_cache:
            features = self.feature_cache[cache_key]
        else:
            # Process data in parallel
            features = await self._parallel_feature_extraction(spectral_data)
            self._update_cache(cache_key, features)
            
        # Preprocess hyperspectral data
        processed_data = self._preprocess_spectral_data(
            spectral_data,
            metadata['wavelength_bands']
        )
        
        # Extract features
        features = self._extract_spectral_features(processed_data)
        
        # Match against database
        matches = self._match_signatures(features)
        
        # Analyze spatial patterns
        spatial_analysis = self._analyze_spatial_patterns(
            processed_data,
            matches
        )
        
        return {
            'detected_signatures': matches,
            'spatial_distribution': spatial_analysis,
            'confidence_scores': self._compute_confidence_scores(matches)
        }
        
    def _preprocess_spectral_data(
        self,
        data: np.ndarray,
        wavelength_bands: List[Tuple[float, float]]
    ) -> np.ndarray:
        # Get environmental conditions from metadata
        atmosphere = self._get_atmospheric_properties()
        weather = self._get_weather_conditions()
        
        # Apply environmental compensation
        wavelengths = np.array([np.mean(band) for band in wavelength_bands])
        compensated_data = self.compensator.compensate_spectral_data(
            data,
            wavelengths,
            atmosphere,
            weather
        )
        
        # Apply existing preprocessing steps
        normalized_data = normalize(compensated_data, axis=1)
        denoised_data = self._reduce_noise(normalized_data)
        
        return denoised_data
        
    def _extract_spectral_features(
        self,
        data: np.ndarray
    ) -> Dict[str, np.ndarray]:
        features = {}
        for name, extractor in self.feature_extractors.items():
            features[name] = extractor(data)
            
        # Add advanced spectral indices
        features.update(self._calculate_spectral_indices(data))
        # Add absorption features
        features.update(self._detect_absorption_features(data))
        
        return features
        
    def _calculate_spectral_indices(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """Calculate various spectral indices for material identification"""
        indices = {}
        
        # Normalized Difference Index for various band combinations
        for band1, band2 in self.wavelength_bands.items():
            for band3, band4 in self.wavelength_bands.items():
                if band1 != band3:
                    name = f"ndi_{band1}_{band3}"
                    indices[name] = self._calculate_ndi(data, band2, band4)
        
        # Add specialized material indices
        indices.update({
            'moisture_content': self._calculate_moisture_index(data),
            'mineral_composition': self._calculate_mineral_index(data),
            'organic_content': self._calculate_organic_index(data)
        })
        
        return indices
        
    def _detect_absorption_features(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """Detect and characterize absorption features in spectral signatures"""
        features = {}
        
        # Continuum removal
        continuum_removed = self._remove_continuum(data)
        
        # Detect absorption bands
        absorption_bands = self._find_absorption_bands(continuum_removed)
        
        # Characterize each absorption feature
        for i, band in enumerate(absorption_bands):
            features[f'absorption_{i}'] = {
                'center': band['center'],
                'depth': band['depth'],
                'width': band['width'],
                'asymmetry': band['asymmetry']
            }
            
        return features
        
    def _match_signatures(self, features: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        matches = []
        
        for sig_id, signature in self.database.signatures.items():
            # Calculate similarity scores using multiple metrics
            similarity_scores = {
                'spectral_angle': self._compute_spectral_angle(features, signature),
                'feature_correlation': self._compute_feature_correlation(features, signature),
                'absorption_match': self._compare_absorption_features(
                    features.get('absorption_features', {}),
                    signature.absorption_features
                ),
                'index_similarity': self._compare_spectral_indices(
                    features.get('spectral_indices', {}),
                    signature.spectral_indices
                )
            }
            
            # Weight and combine scores
            total_score = self._compute_weighted_similarity(similarity_scores)
            
            if total_score >= signature.confidence_threshold:
                matches.append({
                    'signature_id': sig_id,
                    'type': signature.type,
                    'confidence': total_score,
                    'similarity_scores': similarity_scores,
                    'location': self._estimate_location(features['spatial_features'])
                })
        
        return matches
        
    def _analyze_spatial_patterns(
        self,
        data: np.ndarray,
        matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        spatial_analysis = {}
        
        for match in matches:
            # Extract region of interest
            roi = self._extract_roi(data, match['location'])
            
            # Analyze spatial distribution
            spatial_analysis[match['signature_id']] = {
                'distribution': self._compute_spatial_distribution(roi),
                'clustering': self._analyze_clustering(roi),
                'orientation': self._estimate_orientation(roi)
            }
            
        return spatial_analysis
        
    def _compute_confidence_scores(
        self,
        matches: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        return {
            match['signature_id']: self._calculate_confidence(
                match['confidence'],
                match['type']
            )
            for match in matches
        }
        
    async def _parallel_feature_extraction(
        self,
        data: np.ndarray
    ) -> Dict[str, np.ndarray]:
        loop = asyncio.get_event_loop()
        
        # Execute feature extraction in parallel
        tasks = [
            loop.run_in_executor(self.executor, self._extract_thermal_features, data),
            loop.run_in_executor(self.executor, self._extract_em_features, data),
            loop.run_in_executor(self.executor, self._extract_rf_features, data),
            loop.run_in_executor(self.executor, self._extract_spatial_features, data)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            'thermal_profile': results[0],
            'em_emissions': results[1],
            'rf_pattern': results[2],
            'spatial_features': results[3]
        }