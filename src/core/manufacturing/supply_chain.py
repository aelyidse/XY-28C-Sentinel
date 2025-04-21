from typing import Dict, List
import networkx as nx

class SupplyChainModel:
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def build_model(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """Build supply chain network model"""
        self.graph.add_nodes_from([
            (n['id'], {'type': n['type'], 'capacity': n['capacity']}) 
            for n in nodes
        ])
        self.graph.add_edges_from([
            (e['source'], e['target'], {'lead_time': e['lead_time'], 'cost': e['cost']})
            for e in edges
        ])
        
    def optimize_supply_chain(self, demand: Dict) -> Dict[str, Any]:
        """Optimize supply chain for given demand"""
        # Calculate optimal flows
        flow_cost, flow_dict = nx.network_simplex(self.graph)
        
        # Calculate critical paths
        critical_paths = self._find_critical_paths()
        
        return {
            'total_cost': flow_cost,
            'material_flow': flow_dict,
            'critical_paths': critical_paths,
            'bottlenecks': self._identify_bottlenecks()
        }