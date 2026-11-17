from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from backend.models.database import get_db
from backend.models.schemas import Repository, SymbolRecord
from backend.schemas.pydantic_models import TestGenerationRequest
from code_engine.analyzer.test_generator import TestCaseGenerator

router = APIRouter(prefix="/tests", tags=["Test Generation"])

@router.post("/generate")
def generate_unit_tests(payload: TestGenerationRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == payload.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    norm_path = payload.file_path.replace("\\", "/").strip()

    symbol = db.query(SymbolRecord).filter(
        SymbolRecord.repo_id == payload.repo_id,
        SymbolRecord.file_path == norm_path,
        SymbolRecord.name == payload.symbol_name
    ).first()

    sym_dict = {
        "name": payload.symbol_name,
        "signature": symbol.signature if symbol else f"def {payload.symbol_name}()",
        "docstring": symbol.docstring if symbol else "",
        "complexity": symbol.complexity if symbol else 1
    }

    full_p = Path(repo.local_path) / norm_path
    content = ""
    if full_p.exists() and full_p.is_file():
        content = full_p.read_text(encoding="utf-8", errors="replace")

    if payload.framework.lower() == "jest":
        res = TestCaseGenerator.generate_jest(norm_path, sym_dict)
    else:
        res = TestCaseGenerator.generate_pytest(norm_path, sym_dict, content)

    return res

# Compatibility alias
generate_test_cases = generate_unit_tests
TestGenRequest = TestGenerationRequest
