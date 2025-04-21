from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.special import hankel1  # Hankel function for cylindrical wave propagation
from .composite_materials import CompositeMaterial, CompositeLayer

@dataclass
class AtmosphericProperties:
    temperature: float  # K
    pressure: float  # Pa
    humidity: float  # %
    electron_density: np.ndarray  # m^-3
    ion_density: np.ndarray  # m^-3
    conductivity: float  # S/m

@dataclass
class TerrainProperties:
    conductivity: np.ndarray  # S/m
    permittivity: np.ndarray  # relative
    roughness: np.ndarray  # m
    elevation: np.ndarray  # m

@dataclass
class WeatherConditions:
    precipitation_rate: float  # mm/hr
    wind_velocity: np.ndarray  # m/s [u, v, w]
    cloud_coverage: float  # 0-1
    visibility: float  # m
    turbulence_intensity: float  # m²/s³
    solar_flux: Callable[[float], float]  # Time-dependent solar flux (W/m²)
    air_density: float  # kg/m³
    humidity: float  # %
from .electroactive_polymers import ElectroactivePolymerActuator
from .electroactive_polymers import ElectroactivePolymerProperties
from .biomimetic_actuators import BiomimeticActuatorArray

@dataclass
class BiomimeticActuatorConfig:
    actuator_type: str
    properties: ElectroactivePolymerProperties
    array_config: Dict[str, Any]
    control_algorithm: str = 'pid'

@dataclass
class MaterialProperties:
    base_materials: Dict[str, Dict[str, float]]
    composites: Dict[str, CompositeMaterial]
    environmental_factors: Dict[str, float]

class PropagationEnvironment:
    def __init__(self):
        self.c0 = 299792458  # Speed of light in vacuum
        self.mu0 = 4 * np.pi * 1e-7  # Vacuum permeability
        self.epsilon0 = 8.854e-12  # Vacuum permittivity
        self.actuator_arrays: Dict[str, BiomimeticActuatorArray] = {}
        self.material_solver = MaterialSolver()
        
    def add_actuator_array(self, name: str, config: BiomimeticActuatorConfig) -> None:
        """Add a biomimetic actuator array to the environment"""
        actuators = [
            ElectroactivePolymerActuator(config.properties) 
            for _ in range(config.array_config['count'])
        ]
        self.actuator_arrays[name] = BiomimeticActuatorArray(actuators)
        
    def simulate_actuator_response(
        self,
        array_name: str,
        voltages: np.ndarray,
        frequency: float = 0.0
    ) -> Dict[str, Any]:
        """Simulate actuator array response"""
        if array_name not in self.actuator_arrays:
            raise ValueError(f"Actuator array {array_name} not found")
            
        return self.actuator_arrays[array_name].simulate_deformation(
            voltages,
            frequency
        )
    def compute_refractive_index(self, atmosphere: AtmosphericProperties) -> np.ndarray:
        # Complex refractive index calculation
        plasma_freq = np.sqrt(atmosphere.electron_density * 1.6e-19 ** 2 / 
                            (self.epsilon0 * 9.1e-31))
        return np.sqrt(1 - (plasma_freq / (2 * np.pi * self.operating_freq)) ** 2)
    
    async def optimize_material_properties(
        self,
        requirements: Dict[str, Any]
    ) -> CompositeMaterial:
        """Optimize material properties for given environment"""
        result = await self.material_solver.optimize_material(requirements)
        
        # Convert to composite material structure
        layers = [
            CompositeLayer(
                material_type=comp['material']['name'],
                thickness=comp['volume_fraction'] * requirements.get('total_thickness', 10e-3),
                orientation=comp['orientation'],
                properties=comp['material']['properties']
            )
            for comp in result['composition']
        ]
        
        return CompositeMaterial(
            layers=layers,
            stacking_sequence=list(range(len(layers))),
            symmetry='symmetric'
        )


@dataclass
class AtmosphericLayer:
    name: str
    base_altitude: float  # m
    top_altitude: float  # m
    temperature_gradient: float  # K/m
    reference_temperature: float  # K
    reference_pressure: float  # Pa
    composition: Dict[str, float]  # Gas composition percentages

class AtmosphericProperties:
    def __init__(self):
        self.layers = [
            AtmosphericLayer(
                name="troposphere",
                base_altitude=0,
                top_altitude=11000,
                temperature_gradient=-0.0065,
                reference_temperature=288.15,
                reference_pressure=101325,
                composition={"N2": 0.7808, "O2": 0.2095, "Ar": 0.0093, "CO2": 0.0004}
            ),
            # ... other layers (stratosphere, mesosphere, etc.)
        ]
        
    def get_layer_properties(self, altitude: float) -> Dict[str, Any]:
        """Get atmospheric properties at specific altitude"""
        layer = next((l for l in self.layers if l.base_altitude <= altitude < l.top_altitude), None)
        if not layer:
            raise ValueError(f"No atmospheric layer defined for altitude {altitude}m")
            
        # Calculate temperature and pressure using barometric formulas
        temp = layer.reference_temperature + layer.temperature_gradient * (altitude - layer.base_altitude)
        pressure = layer.reference_pressure * (
            (temp / layer.reference_temperature) ** (-self.g0 / (layer.temperature_gradient * self.R))
        )
        
        return {
            "temperature": temp,
            "pressure": pressure,
            "density": pressure / (self.R * temp),
            "composition": layer.composition,
            "layer": layer.name
        }