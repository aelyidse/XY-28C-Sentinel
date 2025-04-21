from .process_planner import ManufacturingProcessPlanner
from .mes import ManufacturingExecutionSystem

class ManufacturingManager:
    def __init__(self, cad_manager, event_manager):
        self.planner = ManufacturingProcessPlanner(cad_manager, event_manager)
        self.mes = ManufacturingExecutionSystem(event_manager)
        
    async def manufacture_component(self, component: str) -> None:
        """Complete manufacturing process for component"""
        plan = await self.planner.generate_manufacturing_plan(component)
        await self.mes.execute_manufacturing_plan(plan)