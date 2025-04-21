import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from scipy.special import jv, hankel1  # Bessel functions for field calculations

@dataclass
class MetamaterialProperties:
    permittivity: np.ndarray  # Frequency-dependent complex permittivity
    permeability: np.ndarray  # Frequency-dependent complex permeability
    conductivity: float
    thickness: float  # mm
    resonant_frequency: float  # Hz
    bandgap_range: Tuple[float, float]  # Hz
    focusing_gain: float
    tuning_range: Tuple[float, float] = (1e9, 6e9)  # Hz
    tuning_sensitivity: float = 0.1  # GHz/volt
    tuning_voltage: float = 0.0  # Current tuning voltage
    tuning_response: Callable = None  # Custom tuning response function

    def apply_tuning(self, voltage: float) -> None:
        """Adjust material properties based on tuning voltage"""
        if self.tuning_response:
            self.tuning_response(voltage)
        else:
            # Default linear tuning response
            freq_shift = (voltage - self.tuning_voltage) * self.tuning_sensitivity * 1e9
            self.resonant_frequency = np.clip(
                self.resonant_frequency + freq_shift,
                *self.tuning_range
            )
            self.tuning_voltage = voltage

from .environment import PropagationEnvironment, AtmosphericProperties, TerrainProperties
from .interference import InterferenceCalculator, EMPSource
from .em_simulator import DirectionalEMPSimulator
from .metamaterial_em import MetamaterialProperties
from .quantum_field import QuantumFieldCalculator

class EMPropagationModel:
    def __init__(self):
        self.c0 = 299792458  # Speed of light in vacuum
        self.mu0 = 4 * np.pi * 1e-7  # Vacuum permeability
        self.epsilon0 = 8.854e-12  # Vacuum permittivity
        self.environment = PropagationEnvironment()
        self.interference_calculator = InterferenceCalculator()
        self.directional_simulator = DirectionalEMPSimulator(self)
        self.quantum_calculator = QuantumFieldCalculator()
        self.operating_freq = 1e9  # Default operating frequency
        self.propagation_distance = 1000  # Default propagation distance
        self.incidence_angle = 0  # Default incidence angle
        
    async def compute_field_propagation(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """
        Compute electromagnetic field propagation
        
        Args:
            params: Dictionary containing parameters for computation:
                - source_strength: Source strength value
                - geometry: Geometry parameters for calculation
                - material_properties: Material properties for metamaterial
                - environment_properties: Properties of propagation environment
                - include_quantum_effects: Whether to include quantum effects
        """
        # Extract parameters
        source_strength = params.get('source_strength', 1.0)
        geometry = params.get('geometry', {})
        material_properties = params.get('material_properties', {})
        environment_properties = params.get('environment_properties', {})
        include_quantum_effects = params.get('include_quantum_effects', False)
        
        # Calculate initial field from explosive-magnetic generator
        primary_field = await self._compute_primary_field(source_strength, geometry)
        
        # Apply metamaterial enhancement
        enhanced_field = await self._apply_metamaterial_effects(
            primary_field,
            material_properties
        )
        
        # Apply quantum field effects if requested
        if include_quantum_effects:
            enhanced_field = await self._apply_quantum_field_effects(
                enhanced_field,
                material_properties,
                params.get('quantum_parameters', {})
        )
        
        # Calculate propagation and attenuation
        propagated_field = await self._compute_propagation(enhanced_field, geometry)
        
        # Apply environmental effects
        propagated_field = await self._apply_environmental_effects(
            enhanced_field,
            environment_properties
        )
        
        result = {
            'primary_field': primary_field,
            'enhanced_field': enhanced_field,
            'propagated_field': propagated_field
        }
        
        # Add quantum metrics if quantum effects were applied
        if include_quantum_effects:
            result['quantum_metrics'] = {
                'coherence_length': self._estimate_coherence_length(
                    enhanced_field, 
                    material_properties
                ),
                'quantum_correction_factor': self._calculate_quantum_correction_factor(
                    primary_field,
                    enhanced_field
                )
            }
        
        return result
        
    async def _compute_primary_field(
        self,
        source_strength: float,
        geometry: Dict[str, Any]
    ) -> np.ndarray:
        # Implement explosive-magnetic generator field calculation
        r = geometry['distance_grid']
        theta = geometry['angle_grid']
        
        # Calculate magnetic field using cylindrical coordinates
        B_phi = (self.mu0 * source_strength) / (2 * np.pi * r)
        # Calculate induced electric field
        E_theta = -r * np.gradient(B_phi, r, axis=0)
        
        return np.stack([B_phi, E_theta])

    async def _apply_metamaterial_effects(
        self,
        primary_field: np.ndarray,
        material_properties: Dict[str, Any]
    ) -> np.ndarray:
        # Create proper MetamaterialProperties object if needed
        if not isinstance(material_properties, MetamaterialProperties):
            material = MetamaterialProperties(
                permittivity=material_properties.get('permittivity', 1.0),
                permeability=material_properties.get('permeability', 1.0),
                resonant_frequency=material_properties.get('resonant_frequency', 1e9),
                focusing_gain=material_properties.get('focusing_gain', 1.0),
                bandwidth=material_properties.get('bandwidth', 1e7),
                tuning_voltage=material_properties.get('tuning_voltage', 0.0)
            )
        else:
            material = material_properties
            
        # Apply metamaterial enhancement and focusing
        omega = 2 * np.pi * material.resonant_frequency
        k = omega * np.sqrt(material.permittivity * material.permeability)
        
        # Calculate metamaterial focusing factor
        focus_factor = material.focusing_gain * np.exp(-1j * k * material_properties.get('thickness', 0.001))
        
        # Apply enhancement to field components
        enhanced_field = primary_field * focus_factor
        
        return enhanced_field
        
    async def _apply_quantum_field_effects(
        self,
        field_data: np.ndarray,
        material_properties: Dict[str, Any],
        quantum_parameters: Dict[str, Any]
    ) -> np.ndarray:
        """Apply quantum field effects to the electromagnetic field"""
        # Set up quantum parameters
        qparams = {
            'add_fluctuations': quantum_parameters.get('add_fluctuations', True),
            'barrier_height': quantum_parameters.get('barrier_height', 1.0),
            'barrier_width': quantum_parameters.get('barrier_width', 1e-9)
        }
        
        # Extract frequency information
        operating_frequency = material_properties.get(
            'operating_frequency', 
            material_properties.get('resonant_frequency', 1e9)
        )
        self.operating_freq = operating_frequency
        
        # Create spatial grid from field data shape
        spatial_dimensions = field_data.shape[:-1]  # Exclude vector components
        spatial_grid = np.meshgrid(*[np.arange(s) for s in spatial_dimensions], indexing='ij')
        spatial_grid = np.stack(spatial_grid, axis=-1)
        
        # Apply quantum corrections
        quantum_corrected_field = self.quantum_calculator.apply_quantum_corrections(
            field_data,
            material_properties
        )
        
        # Add vacuum fluctuations if requested
        if qparams['add_fluctuations']:
            freq_range = (operating_frequency * 0.5, operating_frequency * 1.5)
            fluctuations = self.quantum_calculator.calculate_vacuum_fluctuations(
                freq_range,
                spatial_grid
            )
            quantum_corrected_field = quantum_corrected_field + fluctuations
            
        # Apply quantum tunneling effects for thin metamaterial barriers
        if qparams.get('apply_tunneling', False):
            tunneling_probability = self.quantum_calculator.calculate_quantum_tunneling(
                field_data,
                qparams['barrier_height'],
                qparams['barrier_width']
            )
            
            # Enhance field based on tunneling probability
            tunneling_enhancement = 1.0 + tunneling_probability[..., np.newaxis] * 0.1
            quantum_corrected_field = quantum_corrected_field * tunneling_enhancement
            
        return quantum_corrected_field
        
    def _estimate_coherence_length(self, 
                                field_data: np.ndarray, 
                                material_properties: Dict[str, Any]) -> float:
        """Estimate quantum coherence length based on field properties"""
        # Basic model: coherence length inversely proportional to frequency and temperature
        temperature = material_properties.get('temperature', 300)
        freq = material_properties.get('resonant_frequency', 1e9)
        
        # Approximate coherence length calculation
        thermal_length = self.c0 / (freq * temperature * 1e-10)
        return thermal_length
        
    def _calculate_quantum_correction_factor(self,
                                          primary_field: np.ndarray,
                                          quantum_field: np.ndarray) -> float:
        """Calculate the factor by which quantum effects modify the field"""
        # Calculate field energy densities
        primary_energy = np.mean(np.square(np.linalg.norm(primary_field, axis=0)))
        quantum_energy = np.mean(np.square(np.linalg.norm(quantum_field, axis=0)))
        
        # Return ratio of energies
        return quantum_energy / primary_energy

    async def _compute_propagation(self, 
                                field: np.ndarray, 
                                geometry: Dict[str, Any]) -> np.ndarray:
        """Compute field propagation through space"""
        # Extract propagation parameters
        distance = geometry.get('propagation_distance', 1000)
        self.propagation_distance = distance
        
        # Simple inverse square law attenuation for field magnitude
        distance_grid = geometry.get('distance_grid', np.ones_like(field[0]) * distance)
        attenuation = 1.0 / distance_grid
        
        # Apply attenuation to field
        attenuated_field = field * attenuation[..., np.newaxis]
        
        return attenuated_field

    async def _apply_environmental_effects(
        self,
        field: np.ndarray,
        env_props: Dict[str, Any]
    ) -> np.ndarray:
        if not env_props:
            return field
            
        atmosphere = AtmosphericProperties(**env_props.get('atmosphere', {}))
        terrain = TerrainProperties(**env_props.get('terrain', {}))
        
        # Calculate atmospheric attenuation
        refractive_index = self.environment.compute_refractive_index(atmosphere)
        atmos_attenuation = self._compute_atmospheric_attenuation(
            field, atmosphere, refractive_index
        )
        
        # Calculate terrain effects
        terrain_effects = self._compute_terrain_effects(
            atmos_attenuation, terrain
        )
        
        return terrain_effects
        
    def _compute_atmospheric_attenuation(
        self,
        field: np.ndarray,
        atmosphere: AtmosphericProperties,
        n: np.ndarray
    ) -> np.ndarray:
        # Implement atmospheric attenuation
        k0 = 2 * np.pi * self.operating_freq / self.c0
        k = k0 * n  # Complex propagation constant
        
        # Apply atmospheric losses
        attenuation = np.exp(-k.imag * self.propagation_distance)
        phase_shift = np.exp(-1j * k.real * self.propagation_distance)
        
        return field * attenuation * phase_shift
        
    def _compute_terrain_effects(
        self,
        field: np.ndarray,
        terrain: TerrainProperties
    ) -> np.ndarray:
        # Implement terrain effects using ground wave propagation
        reflection_coeff = self._compute_reflection_coefficient(terrain)
        diffraction = self._compute_diffraction(terrain)
        
        # Combine direct, reflected, and diffracted waves
        total_field = field + field * reflection_coeff + diffraction
        
        return total_field
        
    def _compute_reflection_coefficient(
        self,
        terrain: TerrainProperties
    ) -> np.ndarray:
        # Calculate Fresnel reflection coefficient
        epsilon_r = terrain.permittivity
        sigma = terrain.conductivity
        
        # Complex permittivity
        epsilon_c = epsilon_r - 1j * sigma / (self.operating_freq * self.epsilon0)
        
        # Reflection coefficient for vertical polarization
        theta = self.incidence_angle
        n = np.sqrt(epsilon_c)
        
        R_v = (n * np.cos(theta) - np.sqrt(n**2 - np.sin(theta)**2)) / \
              (n * np.cos(theta) + np.sqrt(n**2 - np.sin(theta)**2))
              
        return R_v
        
    def _compute_diffraction(
        self,
        terrain: TerrainProperties
    ) -> np.ndarray:
        # Implement knife-edge diffraction model
        v = self._compute_fresnel_parameter(terrain.elevation)
        
        # Compute diffraction coefficient using Fresnel integral
        F_v = np.abs(0.5 + 0.5j * hankel1(0, v))
        
        return F_v
        
    def _compute_fresnel_parameter(self, elevation: float) -> float:
        """Calculate Fresnel parameter for diffraction calculation"""
        wavelength = self.c0 / self.operating_freq
        return np.sqrt(2) * elevation / np.sqrt(wavelength * self.propagation_distance)

    async def compute_multi_source_propagation(
        self,
        sources: List[Dict[str, Any]],
        geometry: Dict[str, Any],
        material_properties: Dict[str, Any],
        environment_properties: Dict[str, Any],
        include_quantum_effects: bool = False
    ) -> Dict[str, np.ndarray]:
        # Convert source configurations to EMPSource objects
        emp_sources = []
        for source in sources:
            emp_sources.append(EMPSource(
                position=np.array(source['position']),
                phase=source['phase'],
                amplitude=source['amplitude'],
                frequency=source['frequency'],
                delay=source['delay']
            ))
            
        # Calculate interference pattern
        interference_pattern = self.interference_calculator.compute_interference_pattern(
            emp_sources,
            geometry['observation_grid'],
            geometry['time']
        )
        
        # Apply metamaterial effects to the combined field
        enhanced_field = await self._apply_metamaterial_effects(
            interference_pattern['magnitude'],
            material_properties
        )
        
        # Apply quantum field effects if requested
        if include_quantum_effects:
            enhanced_field = await self._apply_quantum_field_effects(
                enhanced_field,
                material_properties,
                geometry.get('quantum_parameters', {})
        )
        
        final_field = await self._apply_environmental_effects(
            enhanced_field,
            environment_properties
        )
        
        result = {
            'interference_pattern': interference_pattern,
            'enhanced_field': enhanced_field,
            'final_field': final_field,
            'constructive_zones': self._identify_constructive_zones(interference_pattern),
            'destructive_zones': self._identify_destructive_zones(interference_pattern)
        }
        
        # Add quantum metrics if quantum effects were applied
        if include_quantum_effects:
            result['quantum_metrics'] = {
                'coherence_length': self._estimate_coherence_length(
                    enhanced_field, 
                    material_properties
                ),
                'quantum_correction_factor': self._calculate_quantum_correction_factor(
                    interference_pattern['magnitude'],
                    enhanced_field
                )
            }
            
        return result
        
    def _identify_constructive_zones(
        self,
        interference_pattern: Dict[str, np.ndarray]
    ) -> np.ndarray:
        # Identify regions of constructive interference
        magnitude = interference_pattern['magnitude']
        threshold = np.mean(magnitude) + np.std(magnitude)
        return magnitude > threshold
        
    def _identify_destructive_zones(
        self,
        interference_pattern: Dict[str, np.ndarray]
    ) -> np.ndarray:
        # Identify regions of destructive interference
        magnitude = interference_pattern['magnitude']
        threshold = np.mean(magnitude) - np.std(magnitude)
        return magnitude < threshold

    async def compute_directional_propagation(
        self,
        source: Dict[str, Any],
        config: Dict[str, Any],
        metamaterial: Dict[str, Any],
        environment: Dict[str, Any],
        include_quantum_effects: bool = False
    ) -> Dict[str, np.ndarray]:
        """Compute directional EMP propagation with focusing"""
        result = await self.directional_simulator.simulate_focused_emp(
            source,
            config,
            metamaterial,
            environment
        )
        
        # Apply quantum field effects if requested
        if include_quantum_effects and 'final_field' in result:
            quantum_enhanced_field = await self._apply_quantum_field_effects(
                result['final_field'],
                metamaterial,
                environment.get('quantum_parameters', {})
            )
            
            result['quantum_enhanced_field'] = quantum_enhanced_field
            result['quantum_metrics'] = {
                'coherence_length': self._estimate_coherence_length(
                    quantum_enhanced_field, 
                    metamaterial
                ),
                'quantum_correction_factor': self._calculate_quantum_correction_factor(
                    result['final_field'],
                    quantum_enhanced_field
                )
            }
            
        return result
    
    async def compute_altitude_aware_propagation(
        self,
        source_strength: float,
        geometry: Dict[str, Any],
        material_properties: Dict[str, Any],
        environment_properties: Dict[str, Any],
        altitude: float,
        include_quantum_effects: bool = False
    ) -> Dict[str, np.ndarray]:
        """Compute EM propagation with altitude-specific effects"""
        # Adjust for altitude
        altitude_factor = self._altitude_attenuation_factor(altitude)
        
        # Calculate primary field with altitude-adjusted parameters
        primary_field = await self._compute_primary_field(
            source_strength * altitude_factor,
            geometry
        )
        
        # Apply metamaterial effects
        enhanced_field = await self._apply_metamaterial_effects(
            primary_field,
            material_properties
        )
        
        # Apply quantum field effects if requested
        if include_quantum_effects:
            # Adjust quantum parameters based on altitude (thinner atmosphere)
            quantum_parameters = geometry.get('quantum_parameters', {})
            # Increase quantum effects at higher altitudes due to less decoherence
            quantum_parameters['decoherence_factor'] = max(0.1, 1.0 - altitude / 100000)
            
            enhanced_field = await self._apply_quantum_field_effects(
                enhanced_field,
                material_properties,
                quantum_parameters
        )
        
        # Calculate propagation and attenuation
        propagated_field = await self._compute_propagation(enhanced_field, geometry)
        
        # Apply environmental effects with altitude-specific parameters
        if 'atmosphere' in environment_properties:
            # Adjust atmospheric properties based on altitude
            environment_properties['atmosphere']['altitude'] = altitude
            environment_properties['atmosphere']['pressure'] = self._calculate_pressure_at_altitude(altitude)
            environment_properties['atmosphere']['temperature'] = self._calculate_temperature_at_altitude(altitude)
        
        propagated_field = await self._apply_environmental_effects(
            enhanced_field,
            environment_properties
        )
        
        result = {
            'primary_field': primary_field,
            'enhanced_field': enhanced_field,
            'propagated_field': propagated_field,
            'altitude': altitude,
            'altitude_factor': altitude_factor
        }
        
        # Add quantum metrics if quantum effects were applied
        if include_quantum_effects:
            result['quantum_metrics'] = {
                'coherence_length': self._estimate_coherence_length(
                    enhanced_field, 
                    material_properties
                ),
                'quantum_correction_factor': self._calculate_quantum_correction_factor(
                    primary_field,
                    enhanced_field
                )
            }
            
        return result
        
    def _altitude_attenuation_factor(self, altitude: float) -> float:
        """Calculate altitude-dependent attenuation factor"""
        return np.exp(-altitude / 8500)  # Approximate atmospheric scale height
        
    def _calculate_pressure_at_altitude(self, altitude: float) -> float:
        """Calculate atmospheric pressure at given altitude (m)"""
        p0 = 101325  # Standard pressure at sea level (Pa)
        return p0 * np.exp(-altitude / 8500)
        
    def _calculate_temperature_at_altitude(self, altitude: float) -> float:
        """Calculate atmospheric temperature at given altitude (m)"""
        t0 = 288.15  # Standard temperature at sea level (K)
        lapse_rate = 0.0065  # Standard temperature lapse rate (K/m)
        return t0 - lapse_rate * min(altitude, 11000)  # Troposphere model
    
    async def calculate_plasma_attenuation(
        self,
        frequency: float,
        electron_density: float,
        collision_freq: float = 1e9
    ) -> float:
        """Calculate RF attenuation through plasma layer"""
        wp = 8.98 * np.sqrt(electron_density)  # Plasma frequency (Hz)
        if frequency < wp:
            return np.inf  # Total reflection
            
        eps = 1 - (wp/frequency)**2
        conductivity = (electron_density * 1.6e-19**2) / (9.1e-31 * collision_freq)
        alpha = (wp**2 * collision_freq) / (2 * 3e8 * frequency**2 * eps)
        return alpha  # dB/m
        
    async def propagate_through_plasma(
        self,
        signal: np.ndarray,
        frequency: float,
        plasma_params: Dict[str, float]
    ) -> np.ndarray:
        """Propagate signal through plasma sheath"""
        atten = await self.calculate_plasma_attenuation(
            frequency,
            plasma_params['electron_density'],
            plasma_params.get('collision_freq', 1e9)
        )
        
        if np.isinf(atten):
            return np.zeros_like(signal)
            
        distance = plasma_params.get('thickness', 0.1)  # Typical plasma sheath thickness (m)
        return signal * np.exp(-atten * distance)