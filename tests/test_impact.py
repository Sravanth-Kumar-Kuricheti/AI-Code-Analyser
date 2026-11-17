import pytest
import networkx as nx
from code_engine.analyzer.impact_analyzer import ChangeImpactAnalyzer

def test_change_impact_analyzer():
    # Graph: core.py <- service.py <- api.py
    # and tests/test_core.py imports core.py
    graph = nx.DiGraph()
    graph.add_edge("api.py", "service.py")
    graph.add_edge("service.py", "core.py")
    graph.add_edge("tests/test_core.py", "core.py")

    files_ast = [
        {
            "rel_path": "api.py",
            "symbols": [
                {"name": "post_item", "symbol_type": "endpoint", "is_api_endpoint": True, "http_method": "POST", "http_path": "/items"}
            ]
        },
        {"rel_path": "service.py", "symbols": []},
        {"rel_path": "core.py", "symbols": []},
        {"rel_path": "tests/test_core.py", "symbols": []}
    ]

    report = ChangeImpactAnalyzer.analyze_impact("core.py", "", graph, files_ast)
    assert report["blast_radius_score"] in ("HIGH", "CRITICAL", "MEDIUM")
    assert "service.py" in report["affected_files"]
    assert "api.py" in report["affected_files"]
    assert len(report["affected_endpoints"]) >= 1
    assert "tests/test_core.py" in report["affected_tests"]
