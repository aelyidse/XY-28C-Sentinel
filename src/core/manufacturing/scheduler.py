from typing import List, Dict
import numpy as np
from ortools.sat.python import cp_model

class ProductionScheduler:
    def __init__(self):
        self.model = cp_model.CpModel()
        
    def optimize_schedule(self, jobs: List[Dict], resources: Dict) -> Dict[str, Any]:
        """Optimize production schedule using constraint programming"""
        # Create variables
        all_tasks = {}
        for job in jobs:
            for task in job['tasks']:
                start_var = self.model.NewIntVar(0, 10000, f"start_{job['id']}_{task['id']}")
                duration = task['duration']
                end_var = self.model.NewIntVar(0, 10000, f"end_{job['id']}_{task['id']}")
                all_tasks[(job['id'], task['id'])] = {
                    'start': start_var,
                    'end': end_var,
                    'interval': self.model.NewIntervalVar(
                        start_var, duration, end_var, f"interval_{job['id']}_{task['id']}")
                }
        
        # Add constraints
        self._add_precedence_constraints(jobs, all_tasks)
        self._add_resource_constraints(jobs, resources, all_tasks)
        
        # Define objective
        makespan = self.model.NewIntVar(0, 10000, "makespan")
        self.model.AddMaxEquality(makespan, [task['end'] for task in all_tasks.values()])
        self.model.Minimize(makespan)
        
        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        
        if status == cp_model.OPTIMAL:
            return self._extract_schedule(jobs, all_tasks, solver)
        return {}