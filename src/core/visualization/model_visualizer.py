from typing import Dict, Optional
import numpy as np
import open3d as o3d
from ..sensors.reconstruction.model_reconstructor import ModelReconstructor

class ModelVisualizer:
    def __init__(self):
        self.window_name = "3D Model Visualization"
        self.background_color = [0.1, 0.1, 0.1]
        self.point_size = 2
        self.line_width = 1
        
    def visualize_reconstruction(
        self,
        reconstruction_data: Dict[str, Any],
        show_points: bool = True,
        show_normals: bool = False,
        show_wireframe: bool = False
    ):
        # Create visualization window
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name=self.window_name)
        
        # Add reconstructed mesh
        mesh = reconstruction_data['mesh']
        vis.add_geometry(mesh)
        
        if show_points:
            # Add point cloud
            pcd = reconstruction_data['point_cloud']
            pcd.paint_uniform_color([1, 0.706, 0])
            vis.add_geometry(pcd)
            
        if show_normals:
            # Add normal vectors
            normal_vis = self._create_normal_visualization(
                reconstruction_data['point_cloud'],
                reconstruction_data['normals']
            )
            vis.add_geometry(normal_vis)
            
        if show_wireframe:
            # Add wireframe visualization
            wireframe = self._create_wireframe_visualization(mesh)
            vis.add_geometry(wireframe)
            
        # Configure visualization
        self._configure_visualization(vis)
        
        # Run visualization
        vis.run()
        vis.destroy_window()
        
    def _create_normal_visualization(self, pcd, normals):
        # Create lines representing normal vectors
        points = np.asarray(pcd.points)
        normal_endpoints = points + normals * self.normal_scale
        
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(
            np.vstack((points, normal_endpoints))
        )
        line_set.lines = o3d.utility.Vector2iVector(
            [[i, i + len(points)] for i in range(len(points))]
        )
        
        return line_set
        
    def _create_wireframe_visualization(self, mesh):
        # Extract edges from mesh
        edges = mesh.get_edges()
        
        line_set = o3d.geometry.LineSet()
        line_set.points = mesh.vertices
        line_set.lines = edges
        line_set.paint_uniform_color([0, 1, 0])
        
        return line_set