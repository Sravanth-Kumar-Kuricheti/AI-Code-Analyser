from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pathlib import Path

from backend.models.database import get_db
from backend.models.schemas import Repository, FileRecord
from code_engine.parser.ast_parser import ASTParser
from code_engine.dependency.graph_builder import DependencyGraphBuilder
from code_engine.dependency.circular_detector import CircularDependencyDetector
from code_engine.dependency.call_flow import CallFlowTracer

router = APIRouter(prefix="/architecture", tags=["Architecture"])

def _get_repo_ast_and_graph(repo_id: int, db: Session):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    file_recs = db.query(FileRecord).filter(FileRecord.repo_id == repo_id).all()
    files_ast = []
    repo_root = repo.local_path

    for f in file_recs:
        ast_data = ASTParser.parse_file(f.path, repo_root)
        files_ast.append(ast_data)

    builder = DependencyGraphBuilder()
    graph = builder.build_graph(files_ast)
    return repo, files_ast, builder, graph

@router.get("/{repo_id}/graph")
def get_dependency_graph(repo_id: int, db: Session = Depends(get_db)):
    repo, files_ast, builder, graph = _get_repo_ast_and_graph(repo_id, db)
    return {
        "repo_id": repo_id,
        "repo_name": repo.name,
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "graph_data": builder.to_cytoscape_json()
    }

@router.get("/{repo_id}/cycles")
def get_circular_dependencies(repo_id: int, db: Session = Depends(get_db)):
    repo, files_ast, builder, graph = _get_repo_ast_and_graph(repo_id, db)
    cycles = CircularDependencyDetector.detect_cycles(graph)
    return {
        "repo_id": repo_id,
        "has_circular_dependencies": len(cycles) > 0,
        "cycle_count": len(cycles),
        "cycles": cycles
    }

@router.get("/{repo_id}/call-flows")
def get_api_call_flows(repo_id: int, db: Session = Depends(get_db)):
    repo, files_ast, builder, graph = _get_repo_ast_and_graph(repo_id, db)
    flows = CallFlowTracer.trace_endpoint_flows(files_ast, graph)
    return {
        "repo_id": repo_id,
        "endpoint_count": len(flows),
        "flows": flows
    }

# Compatibility alias
get_call_flows = get_api_call_flows
