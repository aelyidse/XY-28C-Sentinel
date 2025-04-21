from typing import Dict, List, Tuple, Optional
import numpy as np
from ..environmental_compensation import EnvironmentalCompensator
from ...physics.models.environment import AtmosphericProperties
from ...physics.models.unified_environment import WeatherConditions, UnifiedEnvironment

class AdaptivePrioritizer:
    def __init__(self):
        self.env_compensator = EnvironmentalCompensator()
        self.base_weights = {
            'lidar': 0.35,
            'magnetic': 0.35,
            'spectral': 0.30
        }
        self.condition_thresholds = {
            'visibility': 1000.0,  # meters
            'precipitation': 25.0,  # mm/hr
            'temperature': 273.15,  # Kelvin
            'em_noise': 0.1  # normalized
        }
        self.threshold_adaptation_rate = 0.05
        self.threshold_history = []
        
        # Add cross-validation parameters
        self.validation_window = 10  # Number of measurements to store for validation
        self.validation_threshold = 0.75  # Minimum correlation threshold
        self.measurement_history = {
            'lidar': [],
            'magnetic': [],
            'spectral': []
        }
        
    def _adjust_thresholds(self, environment: UnifiedEnvironment):
        """Dynamically adjust condition thresholds based on environment"""
        # Update visibility threshold
        if environment.weather.visibility < self.condition_thresholds['visibility']:
            self.condition_thresholds['visibility'] *= (1 - self.threshold_adaptation_rate)
        else:
            self.condition_thresholds['visibility'] *= (1 + self.threshold_adaptation_rate)
            
        # Update precipitation threshold
        if environment.weather.precipitation_rate > self.condition_thresholds['precipitation']:
            self.condition_thresholds['precipitation'] *= (1 + self.threshold_adaptation_rate)
        else:
            self.condition_thresholds['precipitation'] *= (1 - self.threshold_adaptation_rate)
            
        # Keep thresholds within reasonable bounds
        self._constrain_thresholds()
        
    def calculate_sensor_priorities(
        self,
        environment: UnifiedEnvironment,
        sensor_health: Dict[str, float]
    ) -> Dict[str, float]:
        # Calculate environmental impact factors
        env_factors = self._evaluate_environmental_impact(environment)
        
        # Calculate sensor reliability factors
        reliability_factors = self._evaluate_sensor_reliability(
            sensor_health,
            environment
        )
        
        # Combine factors to determine final priorities
        priorities = self._compute_final_priorities(
            env_factors,
            reliability_factors
        )
        
        return priorities
        
    def _evaluate_environmental_impact(
        self,
        environment: UnifiedEnvironment
    ) -> Dict[str, Dict[str, float]]:
        impacts = {}
        
        # LiDAR environmental impacts
        impacts['lidar'] = {
            'visibility': self._calculate_visibility_impact(
                environment.weather.visibility
            ),
            'precipitation': self._calculate_precipitation_impact(
                environment.weather.precipitation_rate
            ),
            'atmospheric': self._calculate_atmospheric_impact(
                environment.atmosphere
            )
        }
        
        # Magnetic sensor environmental impacts
        impacts['magnetic'] = {
            'em_noise': self._calculate_em_noise_impact(
                environment.em_background
            ),
            'temperature': self._calculate_temperature_impact(
                environment.atmosphere.temperature
            )
        }
        
        # Spectral sensor environmental impacts
        impacts['spectral'] = {
            'atmospheric': self._calculate_atmospheric_impact(
                environment.atmosphere
            ),
            'visibility': self._calculate_visibility_impact(
                environment.weather.visibility
            )
        }
        
        return impacts
        
    def _evaluate_sensor_reliability(
        self,
        sensor_health: Dict[str, float],
        environment: UnifiedEnvironment
    ) -> Dict[str, float]:
        reliability = {}
        
        for sensor, health in sensor_health.items():
            # Base reliability from sensor health
            base_reliability = health
            
            # Environmental degradation factor
            env_degradation = self._calculate_environmental_degradation(
                sensor,
                environment
            )
            
            # Combined reliability
            reliability[sensor] = base_reliability * (1.0 - env_degradation)
            
        return reliability
        
    def _compute_final_priorities(
        self,
        env_factors: Dict[str, Dict[str, float]],
        reliability_factors: Dict[str, float]
    ) -> Dict[str, float]:
        priorities = {}
        
        for sensor, base_weight in self.base_weights.items():
            # Calculate environmental impact score
            env_impact = np.mean(list(env_factors[sensor].values()))
            
            # Calculate final priority
            priorities[sensor] = (
                base_weight *
                reliability_factors[sensor] *
                env_impact
            )
            
        # Normalize priorities
        total = sum(priorities.values())
        if total > 0:
            priorities = {k: v/total for k, v in priorities.items()}
            
        return priorities
        
    def _calculate_visibility_impact(self, visibility: float) -> float:
        threshold = self.condition_thresholds['visibility']
        return np.clip(visibility / threshold, 0.1, 1.0)
        
    def _calculate_precipitation_impact(self, precipitation: float) -> float:
        threshold = self.condition_thresholds['precipitation']
        return np.clip(1.0 - precipitation / threshold, 0.1, 1.0)
        
    def _calculate_atmospheric_impact(
        self,
        atmosphere: AtmosphericProperties
    ) -> float:
        # Consider temperature, pressure, and humidity
        temp_factor = atmosphere.temperature / self.condition_thresholds['temperature']
        pressure_factor = atmosphere.pressure / 101325.0  # Standard pressure
        humidity_factor = 1.0 - (atmosphere.humidity / 100.0)
        
        return np.clip(
            np.mean([temp_factor, pressure_factor, humidity_factor]),
            0.1,
            1.0
        )
        
    def _calculate_em_noise_impact(
        self,
        em_background: Dict[str, np.ndarray]
    ) -> float:
        # Calculate normalized noise level
        noise_level = np.mean([
            np.mean(data) for data in em_background.values()
        ])
        
        threshold = self.condition_thresholds['em_noise']
        return np.clip(1.0 - noise_level / threshold, 0.1, 1.0)
        
    def _calculate_environmental_degradation(
        self,
        sensor: str,
        environment: UnifiedEnvironment
    ) -> float:
        degradation_factors = {
            'lidar': lambda: 0.2 * (1.0 - self._calculate_visibility_impact(
                environment.weather.visibility
            )),
            'magnetic': lambda: 0.3 * self._calculate_em_noise_impact(
                environment.em_background
            ),
            'spectral': lambda: 0.25 * (1.0 - self._calculate_atmospheric_impact(
                environment.atmosphere
            ))
        }
        
        return degradation_factors.get(sensor, lambda: 0.0)()
    
    def cross_validate_sensors(
        self,
        measurements: Dict[str, np.ndarray],
        environment: UnifiedEnvironment
    ) -> Dict[str, Dict[str, float]]:
        """
        Perform cross-validation between different sensor types.
        Returns correlation scores between sensor pairs.
        """
        # Update measurement history
        for sensor, data in measurements.items():
            self.measurement_history[sensor].append(data)
            if len(self.measurement_history[sensor]) > self.validation_window:
                self.measurement_history[sensor].pop(0)
                
        validation_scores = {}
        
        # Calculate cross-correlation between sensor pairs
        for sensor1 in self.base_weights.keys():
            validation_scores[sensor1] = {}
            for sensor2 in self.base_weights.keys():
                if sensor1 != sensor2:
                    correlation = self._calculate_sensor_correlation(
                        sensor1,
                        sensor2,
                        environment
                    )
                    validation_scores[sensor1][sensor2] = correlation
                    
        return validation_scores
        
    def _calculate_sensor_correlation(
        self,
        sensor1: str,
        sensor2: str,
        environment: UnifiedEnvironment
    ) -> float:
        """Calculate correlation between two sensor types with environmental compensation."""
        if not (self.measurement_history[sensor1] and self.measurement_history[sensor2]):
            return 0.0
            
        # Get recent measurements
        data1 = np.array(self.measurement_history[sensor1])
        data2 = np.array(self.measurement_history[sensor2])
        
        # Apply environmental compensation
        comp_data1 = self._compensate_measurements(sensor1, data1, environment)
        comp_data2 = self._compensate_measurements(sensor2, data2, environment)
        
        # Calculate correlation with confidence weighting
        correlation = self._weighted_correlation(
            comp_data1,
            comp_data2,
            self._calculate_confidence_weights(sensor1, sensor2, environment)
        )
        
        return np.clip(correlation, 0.0, 1.0)
        
    def _compensate_measurements(
        self,
        sensor_type: str,
        data: np.ndarray,
        environment: UnifiedEnvironment
    ) -> np.ndarray:
        """Apply environmental compensation to sensor measurements."""
        if sensor_type == 'spectral':
            return self.env_compensator.compensate_spectral_data(
                data,
                np.linspace(380e-9, 740e-9, data.shape[-1]),  # Visible spectrum
                environment.atmosphere,
                environment.weather
            )
        elif sensor_type == 'lidar':
            # Compensate for atmospheric effects on LiDAR
            visibility_factor = self._calculate_visibility_impact(
                environment.weather.visibility
            )
            return data * visibility_factor
        else:  # magnetic
            # Compensate for EM background noise
            em_factor = self._calculate_em_noise_impact(
                environment.em_background
            )
            return data * em_factor
            
    def _weighted_correlation(
        self,
        data1: np.ndarray,
        data2: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """Calculate weighted correlation coefficient between two datasets."""
        # Normalize data
        norm1 = (data1 - np.mean(data1)) / (np.std(data1) + 1e-8)
        norm2 = (data2 - np.mean(data2)) / (np.std(data2) + 1e-8)
        
        # Calculate weighted correlation
        weighted_cov = np.sum(weights * norm1 * norm2)
        weighted_std1 = np.sqrt(np.sum(weights * norm1 * norm1))
        weighted_std2 = np.sqrt(np.sum(weights * norm2 * norm2))
        
        return weighted_cov / (weighted_std1 * weighted_std2 + 1e-8)
        
    def _calculate_confidence_weights(
        self,
        sensor1: str,
        sensor2: str,
        environment: UnifiedEnvironment
    ) -> np.ndarray:
        """Calculate confidence weights for correlation based on environmental conditions."""
        # Get environmental impact factors
        env_factors = self._evaluate_environmental_impact(environment)
        
        # Calculate combined confidence
        confidence1 = np.mean(list(env_factors[sensor1].values()))
        confidence2 = np.mean(list(env_factors[sensor2].values()))
        
        # Generate weights based on combined confidence
        weights = np.ones(self.validation_window)
        weights *= np.minimum(confidence1, confidence2)
        
        # Apply temporal decay
        temporal_decay = np.exp(-np.arange(self.validation_window)[::-1] / 5)
        weights *= temporal_decay
        
        return weights / np.sum(weights)