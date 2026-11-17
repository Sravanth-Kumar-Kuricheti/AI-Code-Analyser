from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import Repository, FileRecord
from code_engine.parser.ast_parser import ASTParser
from code_engine.analyzer.tech_debt_analyzer import TechDebtAnalyzer
from ai_engine.llm.client import llm_client

router = APIRouter(prefix="/tech-debt", tags=["Technical Debt"])

class RefactorRequest(BaseModel):
    repo_id: int
    file_path: str
    symbol_name: str
    issue_description: str = ""

@router.get("/{repo_id}")
def get_technical_debt(repo_id: int, db: Session = Depends(get_db)):
    """Computes technical debt, code smells, complexity, and maintainability index."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    file_recs = db.query(FileRecord).filter(FileRecord.repo_id == repo_id).all()
    files_ast = []
    repo_root = repo.local_path

    for f in file_recs:
        ast_data = ASTParser.parse_file(f.path, repo_root)
        files_ast.append(ast_data)

    report = TechDebtAnalyzer.analyze_repository(files_ast)
    report["repo_id"] = repo_id
    report["repo_name"] = repo.name
    return report

@router.post("/refactor")
def refactor_code_routine(req: RefactorRequest, db: Session = Depends(get_db)):
    """
    Leverages Groq Llama-3.3 LLM to refactor a complex method or oversized function
    according to clean code principles (Extract Method, Single Responsibility, Guard Clauses).
    """
    repo = db.query(Repository).filter(Repository.id == req.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    full_path = Path(repo.local_path) / req.file_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File {req.file_path} not found")

    content = full_path.read_text(encoding="utf-8", errors="ignore")
    parsed = ASTParser.parse_file(str(full_path), repo.local_path)

    target_sym = next((s for s in parsed.get("symbols", []) if s.get("name") == req.symbol_name), None)
    lines = content.splitlines()

    if target_sym:
        start = max(1, target_sym.get("line_start", 1))
        end = min(len(lines), target_sym.get("line_end", len(lines)))
        snippet = "\n".join(lines[start - 1:end])
        comp = target_sym.get("complexity", 1)
        loc = end - start + 1
    else:
        snippet = "\n".join(lines[:60])
        comp = 5
        loc = len(lines)

    sys_prompt, user_prompt = TechDebtAnalyzer.build_refactor_prompt(
        code_snippet=snippet,
        symbol_name=req.symbol_name,
        file_path=req.file_path,
        issue_description=req.issue_description
    )
    advice = llm_client.generate(sys_prompt, user_prompt)

    return {
        "symbol_name": req.symbol_name,
        "file_path": req.file_path,
        "original_loc": loc,
        "original_complexity": comp,
        "original_code": snippet,
        "refactored_advice": advice
    }
