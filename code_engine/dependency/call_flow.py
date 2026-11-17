from typing import List, Dict, Any, Tuple
import networkx as nx

def _get_downstream_files(graph: nx.DiGraph, rel_path: str) -> List[str]:
    """Retrieves direct and transitive downstream modules."""
    if not graph.has_node(rel_path):
        return []
    direct = list(graph.successors(rel_path))
    try:
        transitive = list(nx.descendants(graph, rel_path))
    except Exception:
        transitive = []
    return list(dict.fromkeys(direct + transitive))

def _categorize_layers(downstream: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Partitions downstream files into services, models, utils, and others."""
    services = [f for f in downstream if "service" in f.lower() or "logic" in f.lower()]
    models = [f for f in downstream if any(k in f.lower() for k in ("model", "schema", "db", "database"))]
    utils = [f for f in downstream if any(k in f.lower() for k in ("util", "helper", "config"))]
    others = [f for f in downstream if f not in services and f not in models and f not in utils]
    return services, models, utils, others

def _build_endpoint_flow(rel_path: str, sym: Dict[str, Any], graph: nx.DiGraph) -> Dict[str, Any]:
    """Constructs a single endpoint flow trace mapping."""
    method = sym.get("http_method", "GET")
    route_path = sym.get("http_path", "/")
    downstream = _get_downstream_files(graph, rel_path)
    services, models, utils, others = _categorize_layers(downstream)

    layer_flow = [rel_path] + services + models
    return {
        "endpoint": f"{method} {route_path}",
        "method": method,
        "path": route_path,
        "handler": sym.get("name"),
        "file": rel_path,
        "line": sym.get("line_start"),
        "call_chain": layer_flow,
        "services": services,
        "models": models,
        "utilities": utils,
        "other_dependencies": others
    }

class CallFlowTracer:
    """Traces API request flows from controllers/routes to services, models, and databases."""

    @staticmethod
    def trace_endpoint_flows(files_ast: List[Dict[str, Any]], graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Extracts call flows for all detected HTTP endpoints."""
        flows = []
        for f in files_ast:
            rel_path = f.get("rel_path", "").replace("\\", "/")
            for sym in f.get("symbols", []):
                if sym.get("is_api_endpoint"):
                    flows.append(_build_endpoint_flow(rel_path, sym, graph))
        return flows
