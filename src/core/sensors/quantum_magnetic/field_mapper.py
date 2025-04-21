from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from .quantum_sensor import QuantumMagneticSensor

class MagneticFieldMapper:
    def __init__(self, grid_resolution: Tuple[int, int, int] = (50, 50, 20)):
        self.grid_resolution = grid_resolution
        self.interpolation_method = 'cubic'
        self.smoothing_sigma = 1.0
        
    def generate_field_map(
        self,
        measurements: List[Dict[str, np.ndarray]],
        sensor_positions: np.ndarray
    ) -> Dict[str, np.ndarray]:
        # Create regular grid for interpolation
        grid_x, grid_y, grid_z = self._create_spatial_grid(sensor_positions)
        
        # Extract field components
        field_components = self._extract_field_components(measurements)
        
        # Interpolate field values
        interpolated_field = self._interpolate_field(
            field_components,
            sensor_positions,
            (grid_x, grid_y, grid_z)
        )
        
        # Calculate field derivatives and characteristics
        field_characteristics = self._calculate_field_characteristics(
            interpolated_field,
            (grid_x, grid_y, grid_z)
        )
        
        return {
            'field_map': interpolated_field,
            'characteristics': field_characteristics,
            'grid_coordinates': (grid_x, grid_y, grid_z)
        }
        
    def visualize_field(
        self,
        field_map: Dict[str, np.ndarray],
        plot_type: str = '3d_vector'
    ) -> None:
        if plot_type == '3d_vector':
            self._plot_3d_vector_field(field_map)
        elif plot_type == 'contour':
            self._plot_contour_map(field_map)
        elif plot_type == 'streamlines':
            self._plot_field_streamlines(field_map)
            
    def _create_spatial_grid(
        self,
        sensor_positions: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        x_min, y_min, z_min = np.min(sensor_positions, axis=0)
        x_max, y_max, z_max = np.max(sensor_positions, axis=0)
        
        x = np.linspace(x_min, x_max, self.grid_resolution[0])
        y = np.linspace(y_min, y_max, self.grid_resolution[1])
        z = np.linspace(z_min, z_max, self.grid_resolution[2])
        
        return np.meshgrid(x, y, z, indexing='ij')
        
    def _interpolate_field(
        self,
        field_components: Dict[str, np.ndarray],
        sensor_positions: np.ndarray,
        grid: Tuple[np.ndarray, np.ndarray, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        interpolated = {}
        grid_points = np.vstack([grid[0].ravel(), grid[1].ravel(), grid[2].ravel()]).T
        
        for component, values in field_components.items():
            interpolated_values = griddata(
                sensor_positions,
                values,
                grid_points,
                method=self.interpolation_method
            )
            
            # Reshape and smooth
            interpolated[component] = gaussian_filter(
                interpolated_values.reshape(self.grid_resolution),
                sigma=self.smoothing_sigma
            )
            
        return interpolated
        
    def _calculate_field_characteristics(
        self,
        field: Dict[str, np.ndarray],
        grid: Tuple[np.ndarray, np.ndarray, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        dx = np.gradient(grid[0])[0]
        dy = np.gradient(grid[1])[1]
        dz = np.gradient(grid[2])[2]
        
        # Calculate field gradient
        gradient = {
            'x': np.gradient(field['Bx'], dx, dy, dz),
            'y': np.gradient(field['By'], dx, dy, dz),
            'z': np.gradient(field['Bz'], dx, dy, dz)
        }
        
        # Calculate field magnitude
        magnitude = np.sqrt(
            field['Bx']**2 + field['By']**2 + field['Bz']**2
        )
        
        # Calculate divergence
        divergence = (
            gradient['x'][0] +
            gradient['y'][1] +
            gradient['z'][2]
        )
        
        # Calculate curl
        curl = np.array([
            gradient['z'][1] - gradient['y'][2],
            gradient['x'][2] - gradient['z'][0],
            gradient['y'][0] - gradient['x'][1]
        ])
        
        return {
            'magnitude': magnitude,
            'gradient': gradient,
            'divergence': divergence,
            'curl': curl
        }
        
    def _plot_3d_vector_field(self, field_map: Dict[str, np.ndarray]) -> None:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        grid_x, grid_y, grid_z = field_map['grid_coordinates']
        
        # Plot vector field
        ax.quiver(
            grid_x[::2, ::2, ::2],
            grid_y[::2, ::2, ::2],
            grid_z[::2, ::2, ::2],
            field_map['field_map']['Bx'][::2, ::2, ::2],
            field_map['field_map']['By'][::2, ::2, ::2],
            field_map['field_map']['Bz'][::2, ::2, ::2],
            length=0.1,
            normalize=True
        )
        
        # Add field strength colormap
        magnitude = field_map['characteristics']['magnitude']
        scatter = ax.scatter(
            grid_x.ravel(),
            grid_y.ravel(),
            grid_z.ravel(),
            c=magnitude.ravel(),
            cmap='viridis',
            alpha=0.1
        )
        plt.colorbar(scatter, label='Field Strength (T)')
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        plt.title('3D Magnetic Field Map')
        plt.show()