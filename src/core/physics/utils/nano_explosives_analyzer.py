import numpy as np
from typing import Dict, List

class NanoExplosivesAnalyzer:
    @staticmethod
    def calculate_detonation_velocity(
        particle_trajectories: np.ndarray,
        time_points: np.ndarray
    ) -> float:
        """Calculate effective detonation velocity from particle motion"""
        displacements = np.linalg.norm(
            particle_trajectories[-1] - particle_trajectories[0],
            axis=-1
        )
        return np.mean(displacements) / (time_points[-1] - time_points[0])
        
    @staticmethod
    def analyze_composition_efficiency(
        particles: List[Dict[str, Any]],
        energy_results: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Analyze energy release efficiency by particle type"""
        material_types = set(p['material_type'] for p in particles)
        efficiencies = {}
        
        for mat in material_types:
            indices = [i for i, p in enumerate(particles) 
                     if p['material_type'] == mat]
            mat_energy = np.sum(energy_results['total'][:, indices])
            efficiencies[mat] = mat_energy / len(indices)
            
        return efficiencies
        
    @staticmethod
    def calculate_pressure_wave(
        positions: np.ndarray,
        masses: np.ndarray,
        time_step: float
    ) -> np.ndarray:
        """Calculate pressure wave propagation from particle motion"""
        velocities = np.diff(positions, axis=0) / time_step
        momenta = velocities * masses[np.newaxis, :, np.newaxis]
        pressure = np.linalg.norm(momenta, axis=-1)
        return pressure
        
    @staticmethod
    def analyze_nothermite_profile(
        energy_results: Dict[str, np.ndarray],
        particle_types: List[str],
        time_points: np.ndarray
    ) -> Dict[str, Any]:
        """Analyze nanothermite-specific energy release characteristics"""
        thermite_indices = [i for i, t in enumerate(particle_types) 
                          if t == 'nothermite']
        
        if not thermite_indices:
            return {}
            
        thermite_energy = energy_results['total'][:, thermite_indices]
        
        # Calculate energy release rate
        energy_rate = np.gradient(np.sum(thermite_energy, axis=1), time_points)
        
        # Find peak energy release
        peak_idx = np.argmax(energy_rate)
        peak_energy_rate = energy_rate[peak_idx]
        peak_time = time_points[peak_idx]
        
        # Calculate total energy release
        total_energy = np.sum(thermite_energy[-1] - thermite_energy[0])
        
        return {
            'energy_rate': energy_rate,
            'peak_energy_rate': peak_energy_rate,
            'peak_time': peak_time,
            'total_energy': total_energy,
            'energy_profile': thermite_energy
        }
