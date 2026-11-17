from typing import List, Dict, Any
import networkx as nx

class CircularDependencyDetector:
    """
    Identifies circular imports and cyclic dependencies within the repository.
    Generates actionable remediation advice to decouple cyclical modules.
    """

    @staticmethod
    def detect_cycles(graph: nx.DiGraph) -> List[Dict[str, Any]]:
        cycles: List[Dict[str, Any]] = []
        try:
            raw_cycles = list(nx.simple_cycles(graph))
        except Exception:
            raw_cycles = []

        for idx, cycle in enumerate(raw_cycles):
            # cycle is a list of node names: [A, B, C] meaning A -> B -> C -> A
            path_str = " -> ".join(cycle) + f" -> {cycle[0]}"
            severity = "HIGH" if len(cycle) <= 2 else "MEDIUM"
            
            remediation = (
                f"Break cycle by refactoring shared interfaces, models, or types from "
                f"'{cycle[0]}' and '{cycle[1]}' into a dedicated common utility module."
            )
            
            cycles.append({
                "cycle_id": idx + 1,
                "length": len(cycle),
                "nodes": cycle,
                "path_description": path_str,
                "severity": severity,
                "remediation": remediation
            })

        return cycles
