"""
Electromagnetic Field Simulation Module

This module provides electromagnetic field simulation capabilities for the XY-28C-Sentinel system.
"""

import numpy as np
from typing import Dict, Any, Tuple, List, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum

from .models.quantum_field import QuantumFieldCalculator, QuantumFieldParameters
from ..utils.error_handler import SentinelError, ErrorCategory, ErrorSeverity

class EMFieldType(Enum):
    """Types of electromagnetic fields"""
    STATIC = "static"
    HARMONIC = "harmonic"
    PULSED = "pulsed"
    QUANTUM = "quantum"

@dataclass
class EMFieldParameters:
    """Parameters for electromagnetic field simulation"""
    field_type: EMFieldType
    frequency: float = 0.0  # Hz
    amplitude: float = 1.0  # V/m or T
    phase: float = 0.0  # radians
    polarization: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    spatial_resolution: float = 0.01  # meters
    temporal_resolution: float = 1e-9  # seconds
    quantum_effects: bool = True
    boundary_conditions: str = "open"  # open, periodic, reflective

class EMFieldSimulator:
    """Electromagnetic field simulator for XY-28C-Sentinel"""
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize the EM field simulator"""
        self.params = params or {}
        self.quantum_calculator = QuantumFieldCalculator()
        self.field_data = None
        self.grid_dimensions = (0, 0, 0)
        self.time_steps = 0
        self.current_step = 0
        
    async def initialize_simulation(self, 
                                  dimensions: Tuple[int, int, int], 
                                  time_steps: int,
                                  field_params: EMFieldParameters) -> bool:
        """
        Initialize the simulation with specified parameters
        
        Args:
            dimensions: Grid dimensions (x, y, z)
            time_steps: Number of time steps to simulate
            field_params: Field parameters
            
        Returns:
            Success status
        """
        try:
            self.grid_dimensions = dimensions
            self.time_steps = time_steps
            self.field_params = field_params
            
            # Initialize field data array
            self.field_data = np.zeros(dimensions + (3, time_steps))
            
            # Set up initial field configuration
            await self._setup_initial_field()
            
            return True
            
        except Exception as e:
            raise SentinelError(
                f"Failed to initialize EM field simulation: {str(e)}",
                category=ErrorCategory.SOFTWARE,
                severity=ErrorSeverity.ERROR
            )
    
    async def _setup_initial_field(self) -> None:
        """Set up initial field configuration"""
        if self.field_params.field_type == EMFieldType.STATIC:
            # Static field
            self.field_data[..., 0] = self._create_static_field()
            
        elif self.field_params.field_type == EMFieldType.HARMONIC:
            # Harmonic field (initial state)
            self.field_data[..., 0] = self._create_harmonic_field(t=0)
            
        elif self.field_params.field_type == EMFieldType.PULSED:
            # Pulsed field (initial state)
            self.field_data[..., 0] = self._create_pulsed_field(t=0)
            
        elif self.field_params.field_type == EMFieldType.QUANTUM:
            # Quantum field (initial state with fluctuations)
            self.field_data[..., 0] = await self._create_quantum_field()
    
    def _create_static_field(self) -> np.ndarray:
        """Create a static electromagnetic field"""
        field = np.zeros(self.grid_dimensions + (3,))
        
        # Set field direction according to polarization
        for i in range(3):
            field[..., i] = self.field_params.amplitude * self.field_params.polarization[i]
            
        return field
    
    def _create_harmonic_field(self, t: float) -> np.ndarray:
        """Create a harmonic electromagnetic field at time t"""
        field = np.zeros(self.grid_dimensions + (3,))
        
        # Create spatial grid
        x, y, z = np.meshgrid(
            np.arange(self.grid_dimensions[0]),
            np.arange(self.grid_dimensions[1]),
            np.arange(self.grid_dimensions[2]),
            indexing='ij'
        )
        
        # Scale to physical dimensions
        x = x * self.field_params.spatial_resolution
        y = y * self.field_params.spatial_resolution
        z = z * self.field_params.spatial_resolution
        
        # Calculate phase factor
        omega = 2 * np.pi * self.field_params.frequency
        k = omega / 3e8  # Wave number (simplified)
        phase_factor = np.cos(omega * t + k * z + self.field_params.phase)
        
        # Set field components
        for i in range(3):
            field[..., i] = self.field_params.amplitude * self.field_params.polarization[i] * phase_factor
            
        return field
    
    def _create_pulsed_field(self, t: float) -> np.ndarray:
        """Create a pulsed electromagnetic field at time t"""
        # Get harmonic field as base
        field = self._create_harmonic_field(t)
        
        # Apply Gaussian envelope
        pulse_width = self.params.get('pulse_width', 1e-9)  # seconds
        pulse_center = self.params.get('pulse_center', 0)  # seconds
        
        envelope = np.exp(-((t - pulse_center) / pulse_width)**2)
        
        return field * envelope
    
    async def _create_quantum_field(self) -> np.ndarray:
        """Create a quantum electromagnetic field with vacuum fluctuations"""
        # Start with classical field
        if self.field_params.frequency > 0:
            field = self._create_harmonic_field(t=0)
        else:
            field = self._create_static_field()
        
        # Add quantum fluctuations if enabled
        if self.field_params.quantum_effects:
            # Create spatial grid for quantum calculator
            spatial_grid = np.stack(np.meshgrid(
                np.arange(self.grid_dimensions[0]),
                np.arange(self.grid_dimensions[1]),
                np.arange(self.grid_dimensions[2]),
                indexing='ij'
            ), axis=-1)
            
            # Calculate vacuum fluctuations
            freq_range = (0.5 * self.field_params.frequency, 1.5 * self.field_params.frequency)
            if freq_range[0] == 0:
                freq_range = (1e9, 2e9)  # Default range if frequency is zero
                
            fluctuations = self.quantum_calculator.calculate_vacuum_fluctuations(
                freq_range,
                spatial_grid
            )
            
            # Add fluctuations to field
            field = field + fluctuations
            
        return field
    
    async def run_simulation(self) -> Dict[str, Any]:
        """
        Run the electromagnetic field simulation
        
        Returns:
            Simulation results
        """
        try:
            # Initialize progress tracking
            self.current_step = 0
            
            # Prepare material properties for quantum calculations
            material_properties = {
                'permittivity': self.params.get('permittivity', 8.85e-12),
                'permeability': self.params.get('permeability', 1.257e-6),
                'operating_frequency': self.field_params.frequency,
                'temperature': self.params.get('temperature', 300)
            }
            
            # Run simulation for each time step
            for t in range(1, self.time_steps):
                self.current_step = t
                
                # Calculate field at current time step
                await self._calculate_field_step(t, material_properties)
                
                # Allow other tasks to run
                if t % 10 == 0:
                    await asyncio.sleep(0)
            
            # Process results
            return self._process_simulation_results()
            
        except Exception as e:
            raise SentinelError(
                f"Error during EM field simulation: {str(e)}",
                category=ErrorCategory.SOFTWARE,
                severity=ErrorSeverity.ERROR
            )
    
    async def _calculate_field_step(self, t: int, material_properties: Dict[str, Any]) -> None:
        """Calculate field at time step t"""
        dt = self.field_params.temporal_resolution
        physical_time = t * dt
        
        if self.field_params.field_type == EMFieldType.STATIC:
            # Static field doesn't change
            self.field_data[..., t] = self.field_data[..., 0]
            
        elif self.field_params.field_type == EMFieldType.HARMONIC:
            # Update harmonic field
            self.field_data[..., t] = self._create_harmonic_field(physical_time)
            
        elif self.field_params.field_type == EMFieldType.PULSED:
            # Update pulsed field
            self.field_data[..., t] = self._create_pulsed_field(physical_time)
            
        elif self.field_params.field_type == EMFieldType.QUANTUM:
            # For quantum field, use quantum field dynamics
            if t == 1:
                # Initialize quantum simulation
                self.quantum_results = self.quantum_calculator.simulate_quantum_field_dynamics(
                    self.field_data[..., 0],
                    material_properties,
                    duration=self.time_steps * dt,
                    time_steps=self.time_steps
                )
            
            # Copy quantum field evolution to our field data
            self.field_data[..., t] = self.quantum_results['field_evolution'][t]
    
    def _process_simulation_results(self) -> Dict[str, Any]:
        """Process simulation results"""
        # Calculate field energy density
        energy_density = np.sum(self.field_data**2, axis=3)  # Sum over vector components
        
        # Calculate total field energy over time
        total_energy = np.sum(energy_density, axis=(0, 1, 2))
        
        # Calculate field intensity (magnitude)
        field_magnitude = np.sqrt(np.sum(self.field_data**2, axis=3))
        
        # Return results
        return {
            'field_data': self.field_data,
            'energy_density': energy_density,
            'total_energy': total_energy,
            'field_magnitude': field_magnitude,
            'grid_dimensions': self.grid_dimensions,
            'time_steps': self.time_steps,
            'parameters': self.field_params
        }
    
    def get_simulation_progress(self) -> float:
        """Get simulation progress as percentage"""
        if self.time_steps == 0:
            return 0.0
        return 100.0 * self.current_step / self.time_steps