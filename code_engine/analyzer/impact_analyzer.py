from typing import List, Dict, Any, Set, Tuple
import networkx as nx
from pathlib import Path

def _find_affected_files(graph: nx.DiGraph, target_file: str) -> Tuple[List[str], List[str]]:
    """Finds direct predecessors and transitive upstream ancestors."""
    try:
        affected_nodes: Set[str] = set(nx.ancestors(graph, target_file))
    except Exception:
        affected_nodes = set()
    direct_dependents = list(graph.predecessors(target_file))
    affected_files = sorted(list(affected_nodes.union(set(direct_dependents))))
    return direct_dependents, affected_files

def _is_test_importing_target(f: Dict[str, Any], target_file: str) -> bool:
    """Checks if a test file imports the target file module."""
    target_stem = Path(target_file).stem
    for imp in f.get("imports", []):
        mod = imp.get("module", "")
        if target_stem in mod or target_file in mod:
            return True
    return False

def _find_impacted_endpoints_and_tests(all_affected: Set[str], target_file: str, files_ast: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Identifies affected API endpoints and test suites."""
    affected_endpoints, affected_tests = [], []
    for f in files_ast:
        fpath = f.get("rel_path", "")
        if fpath in all_affected:
            for sym in f.get("symbols", []):
                if sym.get("is_api_endpoint"):
                    affected_endpoints.append({
                        "endpoint": sym.get("name"),
                        "file": fpath,
                        "method": sym.get("http_method", ""),
                        "path": sym.get("http_path", "")
                    })
            if "test" in fpath.lower():
                affected_tests.append(fpath)
        elif "test" in fpath.lower() and _is_test_importing_target(f, target_file):
            affected_tests.append(fpath)
    return affected_endpoints, list(set(affected_tests))

def _calculate_blast_score(total_affected: int, endpoint_count: int) -> Tuple[str, str]:
    """Computes blast radius severity tier and badge color."""
    if total_affected == 0:
        return "LOW", "#10B981"
    if total_affected <= 3 and endpoint_count == 0:
        return "MEDIUM", "#F59E0B"
    if total_affected <= 8 or endpoint_count <= 2:
        return "HIGH", "#EF4444"
    return "CRITICAL", "#7C3AED"

class ChangeImpactAnalyzer:
    """Simulates blast radius of proposed code modifications."""

    @staticmethod
    def analyze_impact(
        target_file: str,
        target_symbol: str = "",
        graph: nx.DiGraph = None,
        files_ast: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculates cascading impacts across files, routes, and test suites."""
        if graph is None or not graph.has_node(target_file):
            return {
                "target_file": target_file,
                "target_symbol": target_symbol,
                "blast_radius_score": "LOW",
                "affected_files_count": 0,
                "affected_files": [],
                "affected_endpoints": [],
                "affected_tests": [],
                "risk_assessment": "File is isolated or has no inward dependencies detected."
            }

        direct_dependents, affected_files = _find_affected_files(graph, target_file)
        all_affected = set(affected_files + [target_file])
        affected_endpoints, affected_tests = _find_impacted_endpoints_and_tests(all_affected, target_file, files_ast or [])

        score, color = _calculate_blast_score(len(affected_files), len(affected_endpoints))
        risk_assessment = (
            f"Modifying '{target_file}' will directly affect {len(direct_dependents)} modules "
            f"and cascade to {len(affected_files)} total files across the repository. "
            f"{len(affected_endpoints)} API endpoints and {len(affected_tests)} test files are in the blast path."
        )

        return {
            "target_file": target_file,
            "target_symbol": target_symbol,
            "blast_radius_score": score,
            "badge_color": color,
            "direct_dependents": direct_dependents,
            "affected_files_count": len(affected_files),
            "affected_files": affected_files,
            "affected_endpoints": affected_endpoints,
            "affected_tests": affected_tests,
            "risk_assessment": risk_assessment,
            "recommended_actions": [
                f"Run verification tests: {', '.join(affected_tests) or 'No direct test files found - write a unit test.'}",
                f"Verify downstream endpoints: {', '.join([e['endpoint'] for e in affected_endpoints]) or 'No endpoints impacted.'}",
                "Perform backward-compatibility check on public method signatures."
            ]
        }
