from .ota_updater import OTAUpdater
from .mission_planner import MissionPlanner
from .after_action import AfterActionAnalyzer
from .diagnostics import FieldDiagnostics

class FieldSupportManager:
    def __init__(self, secure_comms, twin_manager, event_manager):
        self.updater = OTAUpdater(secure_comms)
        self.planner = MissionPlanner(twin_manager)
        self.analyzer = AfterActionAnalyzer()
        self.diagnostics = FieldDiagnostics(event_manager)
        
    async def full_support_cycle(self, mission_params: Dict) -> Dict:
        """Run complete field support cycle"""
        # Check and apply updates
        updates = await self.updater.check_for_updates()
        update_results = [await self.updater.apply_update(u) for u in updates]
        
        # Plan and rehearse mission
        plan = await self.planner.plan_mission(mission_params)
        rehearsal = await self.planner.rehearse_mission(plan['primary'])
        
        # Run pre-mission diagnostics
        diag = await self.diagnostics.run_diagnostics(mission_params['system_state'])
        
        return {
            'updates': update_results,
            'mission_plan': plan,
            'rehearsal': rehearsal,
            'diagnostics': diag
        }
        
    async def post_mission_analysis(self, mission_data: Dict) -> Dict:
        """Perform post-mission analysis and improvements"""
        return await self.analyzer.analyze_mission(mission_data)