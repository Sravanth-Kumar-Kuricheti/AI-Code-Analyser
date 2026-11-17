import pytest
import networkx as nx
from code_engine.dependency.graph_builder import DependencyGraphBuilder
from code_engine.dependency.circular_detector import CircularDependencyDetector
from code_engine.dependency.call_flow import CallFlowTracer

def test_dependency_graph_and_cycles():
    files_ast = [
        {
            "rel_path": "module_a.py",
            "language": "python",
            "lines_of_code": 30,
            "symbols": [],
            "imports": [{"module": "module_b", "line": 2}]
        },
        {
            "rel_path": "module_b.py",
            "language": "python",
            "lines_of_code": 40,
            "symbols": [],
            "imports": [{"module": "module_c", "line": 3}]
        },
        {
            "rel_path": "module_c.py",
            "language": "python",
            "lines_of_code": 50,
            "symbols": [],
            "imports": [{"module": "module_a", "line": 1}] # Circular!
        }
    ]

    builder = DependencyGraphBuilder()
    graph = builder.build_graph(files_ast)

    assert graph.number_of_nodes() == 3
    assert graph.has_edge("module_a.py", "module_b.py")
    assert graph.has_edge("module_b.py", "module_c.py")
    assert graph.has_edge("module_c.py", "module_a.py")

    # Detect cycle
    cycles = CircularDependencyDetector.detect_cycles(graph)
    assert len(cycles) >= 1
    assert cycles[0]["length"] == 3

def test_call_flow_tracer():
    files_ast = [
        {
            "rel_path": "routes/user_routes.py",
            "language": "python",
            "symbols": [
                {
                    "name": "create_user",
                    "symbol_type": "endpoint",
                    "is_api_endpoint": True,
                    "http_method": "POST",
                    "http_path": "/users",
                    "line_start": 10
                }
            ],
            "imports": [{"module": "services.user_service"}]
        },
        {
            "rel_path": "services/user_service.py",
            "symbols": [],
            "imports": []
        }
    ]

    builder = DependencyGraphBuilder()
    graph = builder.build_graph(files_ast)
    flows = CallFlowTracer.trace_endpoint_flows(files_ast, graph)

    assert len(flows) == 1
    assert flows[0]["endpoint"] == "POST /users"
    assert "services/user_service.py" in flows[0]["services"]
