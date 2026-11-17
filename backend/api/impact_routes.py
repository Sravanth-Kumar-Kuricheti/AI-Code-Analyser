from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.models.database import get_db
from backend.models.schemas import Repository, FileRecord
from backend.schemas.pydantic_models import ImpactRequest
from code_engine.parser.ast_parser import ASTParser
from code_engine.dependency.graph_builder import DependencyGraphBuilder
from code_engine.analyzer.impact_analyzer import ChangeImpactAnalyzer

router = APIRouter(prefix="/impact", tags=["Change Impact Analysis"])

@router.post("/simulate")
def simulate_change_impact(payload: ImpactRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == payload.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    file_recs = db.query(FileRecord).filter(FileRecord.repo_id == payload.repo_id).all()
    files_ast = []
    repo_root = repo.local_path

    for f in file_recs:
        ast_data = ASTParser.parse_file(f.path, repo_root)
        files_ast.append(ast_data)

    builder = DependencyGraphBuilder()
    graph = builder.build_graph(files_ast)

    norm_target = payload.target_file.replace("\\", "/").strip()

    impact_report = ChangeImpactAnalyzer.analyze_impact(
        target_file=norm_target,
        target_symbol=payload.target_symbol or "",
        graph=graph,
        files_ast=files_ast
    )

    return impact_report
