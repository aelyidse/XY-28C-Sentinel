import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
from scipy.integrate import solve_ivp

@dataclass
class NanoParticle:
    position: np.ndarray  # [x, y, z] in nm
    velocity: np.ndarray  # nm/ps
    mass: float  # atomic mass units
    charge: float  # elementary charge units
    material_type: str  # 'aluminum', 'nothermite', 'cnt'

class NanoExplosivesSimulation:
    def __init__(self, particles: List[NanoParticle], temperature: float = 300.0):
        self.particles = particles
        self.temperature = temperature  # Kelvin
        self.time_step = 0.001  # picoseconds
        self.cutoff_radius = 5.0  # nm
        self.force_field = self._initialize_force_field()
        
    def _initialize_force_field(self) -> Dict[str, Dict[str, float]]:
        """Initialize force field parameters for different material interactions"""
        return {
            'aluminum': {
                'epsilon': 0.5,  # eV
                'sigma': 0.2,    # nm
                'charge': 1.5    # e
            },
            'nothermite': {
                'epsilon': 1.2,  # Increased binding energy for thermite reactions
                'sigma': 0.28,   # Slightly larger atomic radius
                'charge': 2.5,   # Higher charge for oxide formation
                'activation_energy': 0.5,  # eV - energy barrier for reaction
                'reaction_heat': 3.0       # eV - exothermic reaction energy
            },
            'cnt': {
                'epsilon': 0.3,
                'sigma': 0.15,
                'charge': 0.5
            }
        }
        
    def _lennard_jones_potential(self, r: float, epsilon: float, sigma: float) -> float:
        """Calculate Lennard-Jones potential between particles"""
        return 4 * epsilon * ((sigma/r)**12 - (sigma/r)**6)
        
    def _calculate_forces(self) -> np.ndarray:
        """Calculate forces between all particles including thermite reactions"""
        forces = np.zeros((len(self.particles), 3))
        reaction_energy = 0.0
        
        for i, p1 in enumerate(self.particles):
            for j, p2 in enumerate(self.particles[i+1:], i+1):
                r_vec = p2.position - p1.position
                r = np.linalg.norm(r_vec)
                
                if r < self.cutoff_radius:
                    # Check for thermite reaction conditions
                    if (p1.material_type == 'nothermite' and 
                        p2.material_type == 'nothermite' and
                        r < self.force_field['nothermite']['sigma'] * 0.8):
                        
                        # Apply exothermic reaction force
                        reaction_energy += self.force_field['nothermite']['reaction_heat']
                        reaction_force = self._calculate_reaction_force(p1, p2, r_vec)
                        forces[i] += reaction_force
                        forces[j] -= reaction_force
                    else:
                        # Standard LJ and Coulomb forces
                        eps = np.sqrt(self.force_field[p1.material_type]['epsilon'] * 
                                    self.force_field[p2.material_type]['epsilon'])
                        sig = (self.force_field[p1.material_type]['sigma'] + 
                              self.force_field[p2.material_type]['sigma']) / 2
                        lj_force = 24 * eps * (2*(sig/r)**13 - (sig/r)**7) * r_vec/r
                        
                        q1 = self.force_field[p1.material_type]['charge']
                        q2 = self.force_field[p2.material_type]['charge']
                        coulomb_force = 138.935 * q1 * q2 / r**3 * r_vec
                        
                        forces[i] += lj_force + coulomb_force
                        forces[j] -= lj_force + coulomb_force
        
        return forces
        
    def run_simulation(self, duration: float) -> Dict[str, np.ndarray]:
        """Run molecular dynamics simulation"""
        # Initialize positions and velocities
        positions = np.array([p.position for p in self.particles])
        velocities = np.array([p.velocity for p in self.particles])
        
        # Solve equations of motion
        solution = solve_ivp(
            self._equations_of_motion,
            [0, duration],
            np.concatenate([positions.flatten(), velocities.flatten()]),
            t_eval=np.linspace(0, duration, int(duration/self.time_step))
        )
        
        # Process results
        return {
            'positions': solution.y[:3*len(self.particles)].reshape(-1, len(self.particles), 3),
            'velocities': solution.y[3*len(self.particles):].reshape(-1, len(self.particles), 3),
            'time': solution.t,
            'energy': self._calculate_energy(solution.y)
        }
        
    def _equations_of_motion(self, t: float, y: np.ndarray) -> np.ndarray:
        """Equations of motion for the system"""
        n = len(self.particles)
        positions = y[:3*n].reshape(n, 3)
        velocities = y[3*n:].reshape(n, 3)
        
        # Update particle positions for force calculation
        for i, p in enumerate(self.particles):
            p.position = positions[i]
            p.velocity = velocities[i]
            
        forces = self._calculate_forces()
        
        # Calculate accelerations (F = ma)
        accelerations = np.zeros_like(forces)
        for i, p in enumerate(self.particles):
            accelerations[i] = forces[i] / p.mass
            
        return np.concatenate([velocities.flatten(), accelerations.flatten()])
        
    def _calculate_energy(self, y: np.ndarray) -> Dict[str, np.ndarray]:
        """Calculate kinetic, potential and total energy"""
        n = len(self.particles)
        positions = y[:3*n].reshape(n, 3)
        velocities = y[3*n:].reshape(n, 3)
        
        # Kinetic energy
        kinetic = np.array([0.5 * p.mass * np.linalg.norm(v)**2 
                          for p, v in zip(self.particles, velocities)])
        
        # Potential energy
        potential = np.zeros(n)
        for i, p1 in enumerate(self.particles):
            p1.position = positions[i]
            for j, p2 in enumerate(self.particles[i+1:], i+1):
                r = np.linalg.norm(p2.position - p1.position)
                if r < self.cutoff_radius:
                    eps = np.sqrt(self.force_field[p1.material_type]['epsilon'] * 
                                self.force_field[p2.material_type]['epsilon'])
                    sig = (self.force_field[p1.material_type]['sigma'] + 
                          self.force_field[p2.material_type]['sigma']) / 2
                    potential[i] += self._lennard_jones_potential(r, eps, sig)
                    
        return {
            'kinetic': kinetic,
            'potential': potential,
            'total': kinetic + potential
        }