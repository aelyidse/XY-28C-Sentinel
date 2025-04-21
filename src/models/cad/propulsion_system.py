from .parametric_model import ParametricModel

class PropulsionSystemModel(ParametricModel):
    def _validate_parameters(self) -> None:
        required = ['diameter', 'length', 'nozzle_ratio']
        if not all(p in self.parameters for p in required):
            raise ValueError(f"Missing required parameters: {required}")
            
    def generate_geometry(self) -> Dict[str, Any]:
        """Generate propulsion system geometry"""
        # Generate combustion chamber
        chamber = self._generate_combustion_chamber()
        
        # Generate nozzle geometry
        nozzle = self._generate_nozzle()
        
        # Generate MHD accelerator if specified
        mhd = {}
        if 'mhd_length' in self.parameters:
            mhd = self._generate_mhd_accelerator()
            
        return {
            'combustion_chamber': chamber,
            'nozzle': nozzle,
            'mhd_accelerator': mhd
        }
        
    def _generate_combustion_chamber(self) -> Dict[str, float]:
        """Generate combustion chamber geometry"""
        return {
            'diameter': self.parameters['diameter'],
            'length': self.parameters['length'] * 0.6,
            'wall_thickness': self.parameters.get('wall_thickness', 0.02)
        }