from typing import Dict, List
import numpy as np
from ortools.linear_solver import pywraplp

class SupplyChainModel:
    def __init__(self):
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        
    def optimize_supply_chain(self, demand: Dict) -> Dict[str, Any]:
        """Optimize supply chain based on demand forecast"""
        # Create variables
        variables = self._create_supply_variables(demand)
        
        # Add constraints
        self._add_supply_constraints(demand, variables)
        
        # Define objective
        self._set_supply_objective(variables)
        
        # Solve
        status = self.solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL:
            return self._extract_solution(variables)
        return {}
        
    def _create_supply_variables(self, demand: Dict) -> Dict[str, Any]:
        """Create decision variables for supply chain optimization"""
        variables = {}
        for supplier in demand['suppliers']:
            for product in demand['products']:
                var_name = f"{supplier}_{product}"
                variables[var_name] = self.solver.NumVar(
                    0, 
                    demand['max_capacity'][supplier][product], 
                    var_name
                )
        return variables
        
    def _add_supply_constraints(self, demand: Dict, variables: Dict) -> None:
        """Add supply chain constraints"""
        # Demand satisfaction constraints
        for product in demand['products']:
            self.solver.Add(
                sum(variables[f"{s}_{product}"] for s in demand['suppliers']) >= 
                demand['forecast'][product]
            )
            
        # Capacity constraints
        for supplier in demand['suppliers']:
            self.solver.Add(
                sum(variables[f"{supplier}_{p}"] for p in demand['products']) <= 
                demand['total_capacity'][supplier]
            )
            
    def _set_supply_objective(self, variables: Dict) -> None:
        """Set supply chain optimization objective"""
        # Minimize total cost
        self.solver.Minimize(
            sum(
                variables[f"{s}_{p}"] * self._get_unit_cost(s, p)
                for s in self.suppliers
                for p in self.products
            )
        )
        
    def _extract_solution(self, variables: Dict) -> Dict[str, Any]:
        """Extract optimized supply chain solution"""
        solution = {}
        for var_name, var in variables.items():
            if var.solution_value() > 0:
                solution[var_name] = var.solution_value()
        return solution