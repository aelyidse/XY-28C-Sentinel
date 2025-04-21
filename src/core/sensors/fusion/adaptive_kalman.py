from typing import Dict, List, Tuple, Optional
import numpy as np
from filterpy.kalman import UnscentedKalmanFilter
from filterpy.common import Q_discrete_white_noise
from scipy.linalg import block_diag

class AdaptiveKalmanFilter:
    def __init__(self, dim_state: int = 6, dim_meas: int = 3):
        self.dim_state = dim_state
        self.dim_meas = dim_meas
        self.dt = 0.1  # Time step
        self.innovation_window = 10
        self.innovation_history = []
        self.ukf = self._initialize_filter()
        
    def _initialize_filter(self) -> UnscentedKalmanFilter:
        def state_transition_fn(x, dt):
            # State: [x, y, z, vx, vy, vz]
            F = np.array([
                [1, 0, 0, dt, 0, 0],
                [0, 1, 0, 0, dt, 0],
                [0, 0, 1, 0, 0, dt],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1]
            ])
            return F @ x
            
        def measurement_fn(x):
            # Measurement model for position
            H = np.array([
                [1, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0]
            ])
            return H @ x
            
        ukf = UnscentedKalmanFilter(
            dim_x=self.dim_state,
            dim_z=self.dim_meas,
            dt=self.dt,
            fx=state_transition_fn,
            hx=measurement_fn
        )
        
        # Initialize state covariance
        ukf.P = np.eye(self.dim_state) * 0.1
        
        # Initialize process noise
        ukf.Q = block_diag(
            Q_discrete_white_noise(2, self.dt, 0.1),
            Q_discrete_white_noise(2, self.dt, 0.1),
            Q_discrete_white_noise(2, self.dt, 0.1)
        )
        
        # Initialize measurement noise
        ukf.R = np.eye(self.dim_meas) * 0.1
        
        return ukf
        
    def update(
        self,
        measurements: Dict[str, np.ndarray],
        sensor_uncertainties: Dict[str, float]
    ) -> Dict[str, np.ndarray]:
        # Predict step
        self.ukf.predict()
        
        # Adapt measurement noise
        self._adapt_measurement_noise(measurements, sensor_uncertainties)
        
        # Update step with combined measurements
        combined_measurement = self._combine_measurements(measurements)
        self.ukf.update(combined_measurement)
        
        # Store innovation for adaptive filtering
        innovation = combined_measurement - self.ukf.y
        self.innovation_history.append(innovation)
        if len(self.innovation_history) > self.innovation_window:
            self.innovation_history.pop(0)
            
        # Adapt process noise
        self._adapt_process_noise()
        
        return {
            'state': self.ukf.x,
            'covariance': self.ukf.P,
            'innovation': innovation
        }
        
    def _adapt_measurement_noise(
        self,
        measurements: Dict[str, np.ndarray],
        uncertainties: Dict[str, float]
    ):
        # Calculate adaptive measurement noise based on sensor uncertainties
        R_adaptive = np.zeros((self.dim_meas, self.dim_meas))
        
        for sensor, uncertainty in uncertainties.items():
            if sensor in measurements:
                # Scale noise by uncertainty
                R_adaptive += np.eye(self.dim_meas) * uncertainty
                
        # Update measurement noise
        self.ukf.R = R_adaptive
        
    def _adapt_process_noise(self):
        if len(self.innovation_history) < self.innovation_window:
            return
            
        # Calculate innovation covariance
        innovation_cov = np.cov(np.array(self.innovation_history).T)
        
        # Adapt process noise based on innovation statistics
        scale_factor = np.trace(innovation_cov) / (self.dim_meas * self.innovation_window)
        self.ukf.Q *= np.clip(scale_factor, 0.5, 2.0)
        
    def _combine_measurements(
        self,
        measurements: Dict[str, np.ndarray]
    ) -> np.ndarray:
        # Weighted average of measurements based on sensor reliability
        combined = np.zeros(self.dim_meas)
        total_weight = 0
        
        for sensor, measurement in measurements.items():
            weight = self._calculate_measurement_weight(sensor)
            combined += measurement * weight
            total_weight += weight
            
        return combined / total_weight if total_weight > 0 else combined
        
    def _calculate_measurement_weight(self, sensor: str) -> float:
        # Calculate weight based on sensor type and historical performance
        base_weights = {
            'lidar': 0.4,
            'magnetic': 0.3,
            'spectral': 0.3
        }
        return base_weights.get(sensor, 0.1)