import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx

def _is_boundary_match(cand_slash: str, cand_dot: str, rel_no_ext: str, rel_dot: str, candidate: str, rel_lower: str) -> bool:
    """Checks if candidate matches path on exact or segment boundary."""
    if cand_dot == rel_dot or cand_slash == rel_no_ext:
        return True
    if rel_no_ext.endswith("/" + cand_slash) or rel_dot.endswith("." + cand_dot):
        return True
    if "." not in candidate and "/" not in candidate and Path(rel_lower).stem == cand_slash:
        return True
    return False

def _resolve_candidate(candidate: str, file_map: Dict[str, Any]) -> Optional[str]:
    """Resolves an imported module name into a repository file path."""
    if not candidate:
        return None
    if candidate in file_map:
        return file_map[candidate].get("rel_path")

    cand_slash = candidate.replace(".", "/").lower()
    cand_dot = candidate.replace("/", ".").lower()

    for p_data in file_map.values():
        rel = p_data.get("rel_path", "").replace("\\", "/")
        rel_lower = rel.lower()
        rel_no_ext = str(Path(rel_lower).with_suffix(""))
        rel_dot = rel_no_ext.replace("/", ".")
        if _is_boundary_match(cand_slash, cand_dot, rel_no_ext, rel_dot, candidate, rel_lower):
            return rel
    return None

class DependencyGraphBuilder:
    """Constructs file and symbol-level dependency graphs using NetworkX."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def _init_file_nodes(self, files_ast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adds all files as graph nodes and populates path lookup table."""
        file_map: Dict[str, Any] = {}
        for f in files_ast:
            rel = f.get("rel_path", "").replace("\\", "/")
            file_map[rel] = f
            mod_name = rel.replace("/", ".")
            if mod_name.endswith(".py"):
                mod_name = mod_name[:-3]
            file_map[mod_name] = f
            self.graph.add_node(
                rel,
                node_type="file",
                language=f.get("language", "text"),
                loc=f.get("lines_of_code", 0),
                complexity=f.get("cyclomatic_complexity", 1.0),
                symbols_count=len(f.get("symbols", []))
            )
        return file_map

    def _add_import_edge(self, source_file: str, imp: Dict[str, Any], file_map: Dict[str, Any]):
        """Resolves target and adds or increments dependency edge."""
        mod = imp.get("module", "")
        base = imp.get("base_module", "")
        target_file = _resolve_candidate(mod, file_map) or _resolve_candidate(base, file_map)
        if target_file and target_file != source_file:
            if self.graph.has_edge(source_file, target_file):
                self.graph[source_file][target_file]["weight"] += 1
            else:
                self.graph.add_edge(source_file, target_file, edge_type="import", weight=1)

    def build_graph(self, files_ast: List[Dict[str, Any]]) -> nx.DiGraph:
        """Builds directed dependency graph from parsed file AST structures."""
        self.graph.clear()
        file_map = self._init_file_nodes(files_ast)
        for f in files_ast:
            source_file = f.get("rel_path", "").replace("\\", "/")
            for imp in f.get("imports", []):
                self._add_import_edge(source_file, imp, file_map)
        return self.graph

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """Exports graph to standard Cytoscape JSON format."""
        elements = {"nodes": [], "edges": []}
        in_degrees = dict(self.graph.in_degree())
        out_degrees = dict(self.graph.out_degree())

        for node, data in self.graph.nodes(data=True):
            in_d, out_d = in_degrees.get(node, 0), out_degrees.get(node, 0)
            node_path = Path(node)
            parent_name = node_path.parent.name
            label = f"{parent_name}/{node_path.name}" if parent_name and parent_name != "." else node_path.name
            elements["nodes"].append({
                "data": {
                    "id": node,
                    "label": label,
                    "full_path": node,
                    "language": data.get("language", "text"),
                    "loc": data.get("loc", 0),
                    "complexity": data.get("complexity", 1.0),
                    "in_degree": in_d,
                    "out_degree": out_d,
                    "centrality": in_d + out_d
                }
            })

        for edge_id, (u, v, data) in enumerate(self.graph.edges(data=True), 1):
            elements["edges"].append({
                "data": {
                    "id": f"e{edge_id}",
                    "source": u,
                    "target": v,
                    "type": data.get("edge_type", "import"),
                    "weight": data.get("weight", 1)
                }
            })
        return elements
