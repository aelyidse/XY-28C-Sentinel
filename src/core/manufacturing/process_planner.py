from typing import Dict, List
from ..events.event_manager import EventManager
from ..models.cad.cad_manager import CADManager

class ManufacturingProcessPlanner:
    def __init__(self, cad_manager: CADManager, event_manager: EventManager):
        self.cad = cad_manager
        self.event_manager = event_manager
        self.process_templates = self._load_process_templates()
        
    async def generate_manufacturing_plan(self, component: str) -> Dict[str, Any]:
        """Generate manufacturing plan for specified component"""
        # Get CAD model parameters
        model = self.cad.active_models[component]
        params = model.parameters
        
        # Generate process steps
        steps = []
        if component == 'airframe':
            steps = self._generate_airframe_process(params)
        elif component == 'propulsion':
            steps = self._generate_propulsion_process(params)
            
        # Publish manufacturing plan event
        await self.event_manager.publish(SystemEvent(
            event_type=SystemEventType.MANUFACTURING_PLAN_CREATED,
            component_id=f"manufacturing_{component}",
            data={'steps': steps}
        ))
        
        return {'component': component, 'steps': steps}
        
    def _generate_airframe_process(self, params: Dict) -> List[Dict]:
        """Generate airframe manufacturing steps"""
        return [
            {
                'process': 'cnc_machining',
                'machine': '5_axis_cnc',
                'material': 'titanium_alloy',
                'operations': [
                    'rough_milling',
                    'finish_milling',
                    'drilling'
                ],
                'estimated_time': params['length'] * 0.5  # hours per meter
            },
            {
                'process': 'composite_layup',
                'machine': 'automated_fiber_placement',
                'material': 'carbon_fiber',
                'operations': [
                    'surface_prep',
                    'layup',
                    'curing'
                ],
                'estimated_time': params['wingspan'] * 0.3
            }
        ]
        
    def _generate_propulsion_process(self, params: Dict) -> List[Dict]:
        """Generate propulsion system manufacturing steps"""
        steps = [
            {
                'process': 'additive_manufacturing',
                'machine': 'dmls_printer',
                'material': 'inconel_718',
                'operations': [
                    'build_prep',
                    'printing',
                    'stress_relief'
                ],
                'estimated_time': params['length'] * 2.0
            }
        ]
        
        if 'mhd_length' in params:
            steps.append({
                'process': 'precision_assembly',
                'machine': 'clean_room',
                'material': 'ceramic_composite',
                'operations': [
                    'alignment',
                    'bonding',
                    'testing'
                ],
                'estimated_time': params['mhd_length'] * 1.5
            })
            
        return steps