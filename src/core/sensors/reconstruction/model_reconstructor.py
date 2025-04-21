from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
from open3d import geometry, utility, io
from ..lidar.point_cloud_processor import PointCloudProcessor

class ModelReconstructor:
    def __init__(self, resolution: float = 0.05):
        self.resolution = resolution
        self.min_points = 100
        self.normal_radius = 0.1
        self.feature_radius = 0.2
        self.distance_threshold = 0.05
        # Add advanced reconstruction parameters
        self.feature_angle_threshold = 30  # degrees
        self.smoothing_iterations = 3
        self.hole_filling_threshold = 0.1
        self.adaptive_resolution = True
        
    async def reconstruct_3d_model(
        self,
        point_cloud: np.ndarray,
        object_class: Optional[str] = None
    ) -> Dict[str, Any]:
        # Convert to Open3D format
        pcd = self._convert_to_o3d(point_cloud)
        
        # Preprocess point cloud
        processed_pcd = self._preprocess_point_cloud(pcd)
        
        # Estimate normals
        normals = self._estimate_normals(processed_pcd)
        
        # Reconstruct surface
        mesh = self._reconstruct_surface(processed_pcd, normals, object_class)
        
        # Post-process mesh
        final_mesh = self._post_process_mesh(mesh)
        
        return {
            'mesh': final_mesh,
            'point_cloud': processed_pcd,
            'normals': normals,
            'metadata': self._generate_metadata(final_mesh)
        }
        
    def _preprocess_point_cloud(self, pcd):
        # Remove statistical outliers
        pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=20,
            std_ratio=2.0
        )
        
        # Downsample using voxel grid
        pcd = pcd.voxel_down_sample(voxel_size=self.resolution)
        
        # Remove radius outliers
        pcd, _ = pcd.remove_radius_outlier(
            nb_points=16,
            radius=self.normal_radius * 2
        )
        
        # Add adaptive resolution based on curvature
        if self.adaptive_resolution:
            pcd = self._apply_adaptive_sampling(pcd)
        
        return pcd
        
    def _apply_adaptive_sampling(self, pcd):
        """Apply adaptive sampling based on local surface complexity"""
        # Calculate local curvature
        curvatures = self._estimate_curvature(pcd)
        
        # Adjust sampling density based on curvature
        sampling_density = np.clip(
            self.resolution / (1 + 5 * curvatures),
            self.resolution * 0.2,
            self.resolution * 2.0
        )
        
        return self._resample_points(pcd, sampling_density)
        
    def _estimate_curvature(self, pcd):
        """Estimate local surface curvature"""
        # Compute principal curvatures using PCA
        curvatures = []
        points = np.asarray(pcd.points)
        tree = geometry.KDTreeFlann(pcd)
        
        for point in points:
            # Find local neighborhood
            [_, idx, _] = tree.search_radius_vector_3d(point, self.normal_radius)
            if len(idx) < 3:
                curvatures.append(0)
                continue
                
            # Compute local PCA
            neighborhood = points[idx]
            centered = neighborhood - np.mean(neighborhood, axis=0)
            cov = centered.T @ centered
            eigenvals = np.linalg.eigvalsh(cov)
            
            # Estimate curvature from eigenvalues
            curvature = eigenvals[0] / (eigenvals[0] + eigenvals[1] + eigenvals[2])
            curvatures.append(curvature)
            
        return np.array(curvatures)
        
    def _reconstruct_surface(self, pcd, normals, object_class):
        if object_class == "building":
            return self._reconstruct_building(pcd, normals)
        elif object_class == "vehicle":
            return self._reconstruct_vehicle(pcd, normals)
        else:
            return self._reconstruct_general(pcd, normals)
            
    def _reconstruct_general(self, pcd, normals):
        # Enhanced Poisson reconstruction with adaptive depth
        local_complexity = self._estimate_local_complexity(pcd)
        poisson_depth = np.clip(int(9 + np.log2(local_complexity)), 8, 12)
        
        mesh, densities = geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd,
            depth=poisson_depth,
            width=0,
            scale=1.1,
            linear_fit=False
        )
        
        # Adaptive density filtering
        density_threshold = self._compute_adaptive_density_threshold(densities)
        vertices_to_remove = densities < density_threshold
        mesh.remove_vertices_by_mask(vertices_to_remove)
        
        return mesh
        
    def _estimate_local_complexity(self, pcd):
        """Estimate local surface complexity for adaptive reconstruction"""
        # Compute local feature size
        points = np.asarray(pcd.points)
        tree = geometry.KDTreeFlann(pcd)
        
        complexities = []
        for point in points:
            [_, idx, _] = tree.search_radius_vector_3d(point, self.feature_radius)
            if len(idx) < 5:
                complexities.append(1.0)
                continue
                
            # Analyze local geometry
            neighborhood = points[idx]
            complexity = self._analyze_local_geometry(neighborhood)
            complexities.append(complexity)
            
        return np.mean(complexities)
        
    def _analyze_local_geometry(self, points):
        """Analyze local geometric properties"""
        # Compute local geometric measures
        centered = points - np.mean(points, axis=0)
        cov = centered.T @ centered
        eigenvals = np.linalg.eigvalsh(cov)
        
        # Compute shape descriptors
        planarity = (eigenvals[1] - eigenvals[0]) / eigenvals[2]
        sphericity = eigenvals[0] / eigenvals[2]
        linearity = (eigenvals[2] - eigenvals[1]) / eigenvals[2]
        
        # Combine into complexity measure
        return 1.0 - max(planarity, sphericity, linearity)
        
    def _compute_adaptive_density_threshold(self, densities):
        """Compute adaptive density threshold based on distribution"""
        # Use statistical analysis for threshold
        median_density = np.median(densities)
        mad = np.median(np.abs(densities - median_density))
        return median_density - 1.4826 * mad
        
    def _smooth_mesh_preserve_features(self, mesh):
        # Enhanced feature-preserving smoothing
        feature_edges = self._detect_sharp_features(mesh)
        
        # Multi-scale smoothing
        scales = [1.0, 0.5, 0.25]
        for scale in scales:
            lambda_value = 0.5 * scale
            mesh = self._bilateral_smooth(
                mesh,
                feature_edges,
                sigma_distance=self.feature_radius * scale,
                sigma_normal=np.radians(self.feature_angle_threshold),
                lambda_value=lambda_value
            )
            
        return mesh
        
    def _bilateral_smooth(self, mesh, feature_edges, sigma_distance, sigma_normal, lambda_value):
        """Apply bilateral smoothing with feature preservation"""
        vertices = np.asarray(mesh.vertices)
        normals = np.asarray(mesh.vertex_normals)
        
        smoothed_vertices = vertices.copy()
        for i, vertex in enumerate(vertices):
            if i in feature_edges:
                continue
                
            # Find neighbors
            neighbors = self._get_vertex_neighbors(mesh, i)
            if len(neighbors) < 3:
                continue
                
            # Compute bilateral weights
            distances = np.linalg.norm(vertices[neighbors] - vertex, axis=1)
            normal_diffs = 1 - np.abs(np.dot(normals[neighbors], normals[i]))
            
            # Gaussian weights
            distance_weights = np.exp(-distances**2 / (2 * sigma_distance**2))
            normal_weights = np.exp(-normal_diffs**2 / (2 * sigma_normal**2))
            weights = distance_weights * normal_weights
            
            # Apply smoothing
            smoothed_vertices[i] = vertex + lambda_value * (
                np.sum(weights[:, np.newaxis] * (vertices[neighbors] - vertex), axis=0) /
                np.sum(weights)
            )
            
        mesh.vertices = o3d.utility.Vector3dVector(smoothed_vertices)
        return mesh
        
    def _reconstruct_building(self, pcd, normals):
        # Extract planar surfaces
        planes = self._detect_planes(pcd)
        
        # Reconstruct building structure
        mesh = self._reconstruct_architectural_elements(planes)
        
        # Add architectural features
        mesh = self._add_architectural_features(mesh, pcd)
        
        return mesh
        
    def _reconstruct_vehicle(self, pcd, normals):
        # Segment vehicle components
        components = self._segment_vehicle_parts(pcd)
        
        # Reconstruct each component
        meshes = []
        for component in components:
            component_mesh = self._reconstruct_component(component)
            meshes.append(component_mesh)
            
        # Merge component meshes
        final_mesh = self._merge_meshes(meshes)
        
        return final_mesh
        
    def _post_process_mesh(self, mesh):
        # Fill holes
        mesh.fill_holes()
        
        # Remove self-intersecting triangles
        mesh.remove_self_intersecting_triangles()
        
        # Optimize mesh
        mesh.optimize_vertex_positions()
        
        # Smooth mesh while preserving features
        mesh = self._smooth_mesh_preserve_features(mesh)
        
        return mesh